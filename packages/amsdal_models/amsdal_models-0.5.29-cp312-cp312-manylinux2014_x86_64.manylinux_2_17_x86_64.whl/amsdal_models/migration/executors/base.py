import hashlib
from abc import ABC
from abc import abstractmethod
from typing import Any

from amsdal_data.application import AsyncDataApplication
from amsdal_data.application import DataApplication
from amsdal_utils.models.data_models.enums import BaseClasses
from amsdal_utils.models.data_models.enums import MetaClasses
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.schemas.schema import ObjectSchema
from pydantic import BaseModel

from amsdal_models.migration.base_migration_schemas import BaseMigrationSchemas


class FieldDescription(BaseModel):
    """
    Represents a description of a field in a database schema.

    This class holds information about a field, including its name, ID, type,
    and whether it has been marked as deleted.

    Attributes:
        field_name (str): The name of the field.
        field_id (str): The unique identifier of the field.
        field_type (str): The type of the field.
        is_deleted (bool): Indicates whether the field is marked as deleted.
    """

    field_name: str
    field_id: str
    field_type: str
    is_deleted: bool


def _schema_to_table_description(schema: ObjectSchema | None) -> dict[str, str]:
    if not schema or not schema.properties:
        return {}

    return {prop: property_schema.type for prop, property_schema in schema.properties.items()}


def _compare_schemas(previous_scheme: dict[str, str], new_scheme: dict[str, str]) -> list[tuple[str, str, str]]:
    res = []
    for prop_name, prop_type in new_scheme.items():
        if prop_name not in previous_scheme:
            res.append((prop_name, prop_type, 'added'))
            continue

        if prop_type != previous_scheme[prop_name]:
            res.append((prop_name, prop_type, 'changed'))

    for prop_name, prop_type in previous_scheme.items():
        if prop_name not in new_scheme:
            res.append((prop_name, prop_type, 'removed'))

    return res


def _id_for_column(field_name: str, iteration: str | int) -> str:
    return f'f{hashlib.md5(f"{field_name}{iteration}".encode()).hexdigest()}'  # noqa: S324


def _new_table_schemas(
    previous_scheme: ObjectSchema | None,
    new_scheme: ObjectSchema,
    iteration: int,
    existing_table_structure: list[FieldDescription],
) -> None:
    changes = _compare_schemas(_schema_to_table_description(previous_scheme), _schema_to_table_description(new_scheme))

    for field_name, field_type, action in changes:
        if action == 'added':
            existing_table_structure.append(
                FieldDescription(
                    field_name=field_name,
                    field_id=_id_for_column(field_name, iteration),
                    field_type=field_type,
                    is_deleted=False,
                )
            )

        if action == 'changed':
            for column in existing_table_structure:
                if column.field_name == field_name:
                    column.is_deleted = True

            existing_table_structure.append(
                FieldDescription(
                    field_name=field_name,
                    field_id=_id_for_column(field_name, iteration),
                    field_type=field_type,
                    is_deleted=False,
                )
            )

        if action == 'removed':
            for column in existing_table_structure:
                if column.field_name == field_name:
                    column.is_deleted = True


class BaseMigrationExecutor(ABC):
    """
    Abstract base class for executing migration operations on database schemas.

    This class provides methods for creating, updating, and deleting classes in the database schema.
    It also manages schema migration buffers and generates full object schemas based on the migration history.
    """

    schemas: BaseMigrationSchemas

    def __init__(self) -> None:
        self._buffer: list[tuple[str, ObjectSchema, ModuleType, dict[str, Any] | None]] = []
        self._non_flushable_buffer: list[tuple[str, ObjectSchema, ModuleType]] = []

    def generate_full_object_schema(
        self,
        class_name: str,
        object_schema: ObjectSchema,
        buffer: list[tuple[str, ObjectSchema, ModuleType]],
    ) -> list[FieldDescription]:
        """
        Generates the full object schema based on the migration history.

        This method constructs the full object schema for a given class by iterating through
        the migration history buffer and applying schema changes in sequence.

        Args:
            class_name (str): The name of the class for which the schema is being generated.
            object_schema (ObjectSchema): The current object schema.
            buffer (list[tuple[str, ObjectSchema, SchemaTypes]]): The migration history buffer.

        Returns:
            list[FieldDescription]: A list of field descriptions representing the full object schema.
        """
        history = []
        for _class_name, _object_schema, _ in buffer:
            if _class_name == class_name:
                history.append(_object_schema)

            if _object_schema == object_schema:
                break

        prev_schema = None
        existing_table: list[FieldDescription] = []

        for i, schema in enumerate(history):
            _new_table_schemas(prev_schema, schema, i, existing_table)
            prev_schema = schema

        return existing_table

    @abstractmethod
    def create_class(
        self,
        schemas: BaseMigrationSchemas,
        class_name: str,
        object_schema: ObjectSchema,
        module_type: ModuleType,
    ) -> None: ...

    @abstractmethod
    def update_class(
        self,
        schemas: BaseMigrationSchemas,
        class_name: str,
        object_schema: ObjectSchema,
        module_type: ModuleType,
        context: dict[str, Any],
    ) -> None: ...

    @abstractmethod
    def delete_class(
        self,
        schemas: BaseMigrationSchemas,
        class_name: str,
        module_type: ModuleType,
    ) -> None: ...

    def forward_schema(
        self,
        schemas: BaseMigrationSchemas,  # noqa: ARG002
        class_name: str,
        object_schema: ObjectSchema,
        module_type: ModuleType,
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> None:
        """
        Forwards the schema to the non-flushable buffer.

        This method appends the given class name, object schema, and schema type to the
        non-flushable buffer for further processing.

        Args:
            schemas (BaseMigrationSchemas): The migration schemas used for the operations.
            class_name (str): The name of the class for which the schema is being forwarded.
            object_schema (ObjectSchema): The current object schema.
            module_type (ModuleType): The type of the schema.
            context (dict[str, Any] | None): Extra execution context.

        Returns:
            None
        """
        self._non_flushable_buffer.append((class_name, object_schema, module_type))

    @staticmethod
    def _resolve_base_class_name(class_name: str, meta_class: str) -> str:
        _meta_class = MetaClasses(meta_class)

        if _meta_class == MetaClasses.TYPE or class_name == BaseClasses.CLASS_OBJECT:
            return BaseClasses.OBJECT.value
        else:
            return BaseClasses.CLASS_OBJECT.value

    def buffer_class_migration(
        self,
        class_name: str,
        object_schema: ObjectSchema,
        module_type: ModuleType,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Buffers the class migration operation.

        This method appends the given class name, object schema, and schema type to both
        the non-flushable buffer and the main buffer for further processing.

        Args:
            class_name (str): The name of the class for which the migration is being buffered.
            object_schema (ObjectSchema): The current object schema.
            module_type (ModuleType): The type of the schema.
            context (dict[str, Any]): Extra execution context

        Returns:
            None
        """
        self._non_flushable_buffer.append((class_name, object_schema, module_type))
        self._buffer.append((class_name, object_schema, module_type, context))

    def flush_buffer(self) -> None:
        """
        Flushes the migration buffer.

        This method clears all entries from the main migration buffer, effectively
        resetting it for future migration operations.

        Returns:
            None
        """
        self._buffer.clear()
        DataApplication().wait_for_background_tasks()

    @staticmethod
    def _prepare_object_schema_properties(object_schema: ObjectSchema) -> None:
        """Helper to prepare object schema properties"""
        _properties = object_schema.properties or {}
        for prop_name, prop in _properties.items():
            prop.field_name = prop_name
            prop.field_id = prop_name

    @staticmethod
    def _normalize_object_schema_data(data: dict[str, Any]) -> dict[str, Any]:
        _options = data.get('options')
        if _options:
            data['options'] = sorted(_options, key=lambda o: o['key'])

        _required = data.get('required')
        if _required:
            data['required'] = sorted(_required)

        return data


class AsyncBaseMigrationExecutor(BaseMigrationExecutor, ABC):
    async def flush_buffer(self) -> None:  # type: ignore[override]
        """
        Flushes the migration buffer.

        This method clears all entries from the main migration buffer, effectively
        resetting it for future migration operations.

        Returns:
            None
        """
        self._buffer.clear()
        await AsyncDataApplication().wait_for_background_tasks()
