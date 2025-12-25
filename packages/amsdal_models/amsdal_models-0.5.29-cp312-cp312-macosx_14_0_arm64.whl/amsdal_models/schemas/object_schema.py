import ast
import importlib
import inspect
import subprocess
import tempfile
from collections.abc import Mapping
from typing import Any

from amsdal_utils.models.data_models.core import AmsdalGenerateJsonSchema
from amsdal_utils.models.data_models.core import TypeData
from amsdal_utils.models.data_models.core import get_definition
from amsdal_utils.models.data_models.enums import CoreTypes
from amsdal_utils.models.data_models.enums import MetaClasses
from amsdal_utils.schemas.schema import ObjectSchema
from amsdal_utils.schemas.schema import PropertyData
from amsdal_utils.schemas.schema import StorageMetadata

from amsdal_models.classes.data_models.constraints import UniqueConstraint
from amsdal_models.classes.data_models.indexes import IndexInfo
from amsdal_models.classes.model import Model
from amsdal_models.classes.model import TypeModel
from amsdal_models.classes.relationships.constants import DEFERRED_FOREIGN_KEYS
from amsdal_models.classes.relationships.constants import DEFERRED_PRIMARY_KEYS
from amsdal_models.classes.relationships.constants import FOREIGN_KEYS
from amsdal_models.classes.relationships.constants import MANY_TO_MANY_FIELDS
from amsdal_models.classes.relationships.constants import PRIMARY_KEY
from amsdal_models.classes.relationships.constants import PRIMARY_KEY_FIELDS
from amsdal_models.classes.relationships.helpers.deferred_foreign_keys import complete_deferred_foreign_keys
from amsdal_models.classes.relationships.helpers.deferred_many_to_many import complete_deferred_many_to_many
from amsdal_models.classes.relationships.helpers.deferred_primary_keys import complete_deferred_primary_keys
from amsdal_models.classes.relationships.meta.references import build_fk_db_fields
from amsdal_models.classes.relationships.reference_field import ReferenceFieldInfo

_CACHE: dict[type[Model | TypeModel], ObjectSchema] = {}


def find_model_fields_schema(core_schema: Mapping[str, Any]) -> Mapping[str, Any]:
    _schema = core_schema.get('schema', {})

    if _schema.get('type') == 'model-fields':
        return _schema

    return find_model_fields_schema(_schema)


def model_to_object_schema(model: type[Model] | type[TypeModel]) -> ObjectSchema:
    if model in _CACHE:
        return _CACHE[model]

    if not issubclass(model, Model | TypeModel):
        msg = f'{model} is not a Model'
        raise ValueError(msg)

    complete_deferred_primary_keys(model)  # type: ignore[arg-type]
    complete_deferred_foreign_keys(model)  # type: ignore[arg-type]
    complete_deferred_many_to_many(model)  # type: ignore[arg-type]

    _schema = model.model_json_schema(schema_generator=AmsdalGenerateJsonSchema)
    context = {}

    if '$defs' in _schema:
        context['$defs'] = _schema.pop('$defs')

    if '$ref' in _schema:
        _schema = get_definition(context, _schema['$ref'])

    object_schema = ObjectSchema.model_validate(_schema, context=context)
    object_schema.properties = object_schema.properties or {}
    object_schema.custom_code = _model_to_custom_code(model) or None

    storage_metadata = StorageMetadata(
        table_name=model.__table_name__ or model.__name__,
        primary_key=getattr(model, PRIMARY_KEY, None),
        foreign_keys=get_model_foreign_keys(model),
        db_fields={},
    )
    object_schema.storage_metadata = storage_metadata

    for key, value in object_schema.properties.items():
        model_field = model.model_fields[key]

        if isinstance(model_field, ReferenceFieldInfo):
            _db_field = model_field.db_field

            if callable(_db_field):
                _db_field = _db_field(key, model_field.annotation)  # type: ignore[arg-type]

            if isinstance(_db_field, str):
                _db_field = [_db_field]

            storage_metadata.db_fields[key] = _db_field  # type: ignore[assignment,index]
        elif key in storage_metadata.foreign_keys:  # type: ignore[attr-defined]
            storage_metadata.db_fields[key] = list(storage_metadata.foreign_keys[key][0].keys())  # type: ignore[attr-defined,index]

        if (
            _processed_type := _process_model_types(model_field.annotation)  # type: ignore[arg-type]
        ) and _processed_type != value.type:
            value.type = _processed_type

            for _unnecessary_key in ['required', 'properties', 'items']:
                if getattr(value, _unnecessary_key, None):
                    delattr(value, _unnecessary_key)

    m2m_fields = getattr(model, MANY_TO_MANY_FIELDS, None) or {}

    for m2m_prop, (m2m_type, _, _, field_info) in m2m_fields.items():
        object_schema.properties[m2m_prop] = PropertyData(
            title=getattr(field_info, 'title', None),
            type='array',
            items=TypeData(type=m2m_type.__name__),
        )

    _mro = model.mro()
    for cls in _mro[1:]:
        if cls in [Model, TypeModel]:
            break

        if issubclass(cls, Model | TypeModel):
            object_schema.type = cls.__name__
            break

    if not issubclass(model, Model) and issubclass(model, TypeModel):
        object_schema.meta_class = MetaClasses.TYPE.value

    if hasattr(model, '__indexes__'):
        storage_metadata.indexed = [[index.field] for index in model.__indexes__ if isinstance(index, IndexInfo)]
    if hasattr(model, '__constraints__'):
        storage_metadata.unique = [
            index.fields for index in model.__constraints__ if isinstance(index, UniqueConstraint)
        ]

    _CACHE[model] = object_schema

    return object_schema


def get_model_foreign_keys(
    model: type[Model] | type[TypeModel],
) -> dict[str, tuple[dict[str, Any], str, list[str]]]:
    fks: list[str] = getattr(model, FOREIGN_KEYS, None) or []
    fks_info: dict[str, tuple[dict[str, Any], str, list[str]]] = {}

    for _fk in fks:
        field_info = model.model_fields[_fk]
        _recalculate_db_fields = False
        fk_type, db_fields, _ = build_fk_db_fields(_fk, field_info)

        if getattr(fk_type, DEFERRED_PRIMARY_KEYS, None):
            complete_deferred_primary_keys(fk_type)  # type: ignore[arg-type]
            _recalculate_db_fields = True

        if getattr(fk_type, DEFERRED_FOREIGN_KEYS, None):
            complete_deferred_foreign_keys(fk_type)  # type: ignore[arg-type]
            _recalculate_db_fields = True

        if _recalculate_db_fields:
            _, db_fields, _ = build_fk_db_fields(_fk, field_info)

        pk_fields = getattr(fk_type, PRIMARY_KEY_FIELDS, None) or {}
        pks = list(pk_fields.keys())
        class_name = getattr(fk_type, '__table_name__', None) or fk_type.__name__  # type: ignore[union-attr]
        internal_db_fields = {key: CoreTypes.from_python_type(value) for key, value in db_fields.items()}
        fks_info[_fk] = (internal_db_fields, class_name, pks)

    return fks_info


def _process_model_types(t: type) -> str | None:
    try:
        if issubclass(t, Model | TypeModel):
            return t.__name__
    except TypeError:
        return None

    return None


def _model_to_custom_code(model: type[Model] | type[TypeModel]) -> str:
    methods: list[str] = []
    defined_method_names: set[str] = set()
    imports: set[str] = set()

    for model_class in model.mro():
        if model_class in [Model, TypeModel]:
            break

        try:
            module = ast.parse(inspect.getsource(model_class))
        except (IndentationError, OSError):
            # OSError occurs if class is created on the fly
            continue

        class_def: ast.ClassDef = module.body[0]  # type: ignore[assignment]

        for node in class_def.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if node.name in defined_method_names:
                    continue

                defined_method_names.add(node.name)
                methods.append(ast.unparse(node))

        module_type = importlib.import_module(model_class.__module__)

        module = ast.parse(inspect.getsource(module_type))
        for node in module.body:
            if isinstance(node, ast.Import | ast.ImportFrom):
                imports.add(ast.unparse(node))

    method_code = '\n'.join(imports) + '\n' + '\n\n'.join(sorted(methods))

    return _format_code(method_code)


def _format_code(body: str) -> str:
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(body)
        f.flush()

        subprocess.run(  # noqa: S603
            [  # noqa: S607
                'ruff',
                'check',
                '--fix',
                '--select',
                'I,F',
                '--fixable',
                'I,F',
                '-s',
                f.name,
            ],
            check=False,
        )

        with open(f.name) as ff:
            body = ff.read()

    return body.strip()
