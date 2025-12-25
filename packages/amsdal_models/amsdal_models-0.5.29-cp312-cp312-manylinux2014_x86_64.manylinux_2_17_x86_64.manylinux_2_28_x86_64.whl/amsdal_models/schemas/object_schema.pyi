from amsdal_models.classes.data_models.constraints import UniqueConstraint as UniqueConstraint
from amsdal_models.classes.data_models.indexes import IndexInfo as IndexInfo
from amsdal_models.classes.model import Model as Model, TypeModel as TypeModel
from amsdal_models.classes.relationships.constants import DEFERRED_FOREIGN_KEYS as DEFERRED_FOREIGN_KEYS, DEFERRED_PRIMARY_KEYS as DEFERRED_PRIMARY_KEYS, FOREIGN_KEYS as FOREIGN_KEYS, MANY_TO_MANY_FIELDS as MANY_TO_MANY_FIELDS, PRIMARY_KEY as PRIMARY_KEY, PRIMARY_KEY_FIELDS as PRIMARY_KEY_FIELDS
from amsdal_models.classes.relationships.helpers.deferred_foreign_keys import complete_deferred_foreign_keys as complete_deferred_foreign_keys
from amsdal_models.classes.relationships.helpers.deferred_many_to_many import complete_deferred_many_to_many as complete_deferred_many_to_many
from amsdal_models.classes.relationships.helpers.deferred_primary_keys import complete_deferred_primary_keys as complete_deferred_primary_keys
from amsdal_models.classes.relationships.meta.references import build_fk_db_fields as build_fk_db_fields
from amsdal_models.classes.relationships.reference_field import ReferenceFieldInfo as ReferenceFieldInfo
from amsdal_utils.schemas.schema import ObjectSchema
from collections.abc import Mapping
from typing import Any

_CACHE: dict[type[Model | TypeModel], ObjectSchema]

def find_model_fields_schema(core_schema: Mapping[str, Any]) -> Mapping[str, Any]: ...
def model_to_object_schema(model: type[Model] | type[TypeModel]) -> ObjectSchema: ...
def get_model_foreign_keys(model: type[Model] | type[TypeModel]) -> dict[str, tuple[dict[str, Any], str, list[str]]]: ...
def _process_model_types(t: type) -> str | None: ...
def _model_to_custom_code(model: type[Model] | type[TypeModel]) -> str: ...
def _format_code(body: str) -> str: ...
