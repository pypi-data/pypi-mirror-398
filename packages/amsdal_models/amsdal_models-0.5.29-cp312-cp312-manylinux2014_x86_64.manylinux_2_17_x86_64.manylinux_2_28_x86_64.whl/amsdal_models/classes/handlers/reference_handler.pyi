import json
import typing_extensions
from amsdal_models.classes.handlers.object_id_handler import ObjectIdHandler as ObjectIdHandler
from amsdal_models.classes.relationships.constants import FOREIGN_KEYS as FOREIGN_KEYS, MANY_TO_MANY_FIELDS as MANY_TO_MANY_FIELDS
from amsdal_models.classes.utils import object_id_to_internal as object_id_to_internal
from amsdal_models.errors import AmsdalTypeError as AmsdalTypeError
from amsdal_utils.models.data_models.reference import Reference
from pydantic_core.core_schema import SerializationInfo as SerializationInfo, SerializerFunctionWrapHandler as SerializerFunctionWrapHandler
from typing import Any, Literal

IncEx: typing_extensions.TypeAlias
SERIALIZE_WITH_REFS_FLAG: str
EXCLUDE_M2M_FIELDS_FLAG: str
STACK_CONTEXT_FLAG: str

def _serialize_type_model_field_value(field_value: Any, field_name: str) -> Any: ...

class ReferenceHandler(ObjectIdHandler):
    def build_reference(self, *, is_frozen: bool = False) -> Reference:
        """
        Reference of the object/record. It's always referenced to latest object version.

        Returns:
            Reference: The reference of the object/record.
        """
    async def abuild_reference(self, *, is_frozen: bool = False) -> Reference:
        """
        Reference of the object/record. It's always referenced to latest object version.

        Returns:
            Reference: The reference of the object/record.
        """
    def ser_model(self, nxt: SerializerFunctionWrapHandler, info: SerializationInfo) -> dict[str, Any]:
        """
        Serializes the model.

        Returns:
            dict[str, Any]: The serialized model as a dictionary.
        """
    def model_dump_refs(self, *, mode: Literal['json', 'python'] | str = 'python', include: IncEx = None, exclude: IncEx = None, by_alias: bool = False, context: Any | None = None, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False, round_trip: bool = False, warnings: bool = True, serialize_as_any: bool = False) -> dict[str, Any]:
        """
        Dumps the model with references.

        Args:
            mode (Literal['json', 'python'] | str, optional): The mode of serialization. Defaults to 'python'.
            include (IncEx, optional): Fields to include in the serialization. Defaults to None.
            exclude (IncEx, optional): Fields to exclude from the serialization. Defaults to None.
            context (Any | None, optional): The context of the serialization. Defaults to None.
            by_alias (bool, optional): Whether to use field aliases. Defaults to False.
            exclude_unset (bool, optional): Whether to exclude unset fields. Defaults to False.
            exclude_defaults (bool, optional): Whether to exclude fields with default values. Defaults to False.
            exclude_none (bool, optional): Whether to exclude fields with None values. Defaults to False.
            round_trip (bool, optional): Whether to ensure round-trip serialization. Defaults to False.
            warnings (bool, optional): Whether to show warnings. Defaults to True.
            serialize_as_any (bool, optional): Whether to serialize as Any. Defaults to False.

        Returns:
            dict[str, Any]: The serialized model as a dictionary.
        """
    async def amodel_dump_refs(self, **kwargs) -> dict[str, Any]: ...
    def model_dump(self, *, mode: Literal['json', 'python'] | str = 'python', include: IncEx = None, exclude: IncEx = None, context: Any | None = None, by_alias: bool = False, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False, round_trip: bool = False, warnings: bool = True, serialize_as_any: bool = False) -> dict[str, Any]:
        """
        Dumps the model.

        Args:
            mode (Literal['json', 'python'] | str, optional): The mode of serialization. Defaults to 'python'.
            include (IncEx, optional): Fields to include in the serialization. Defaults to None.
            exclude (IncEx, optional): Fields to exclude from the serialization. Defaults to None.
            context (Any | None, optional): The context of the serialization. Defaults to None.
            by_alias (bool, optional): Whether to use field aliases. Defaults to False.
            exclude_unset (bool, optional): Whether to exclude unset fields. Defaults to False.
            exclude_defaults (bool, optional): Whether to exclude fields with default values. Defaults to False.
            exclude_none (bool, optional): Whether to exclude fields with None values. Defaults to False.
            round_trip (bool, optional): Whether to ensure round-trip serialization. Defaults to False.
            warnings (bool, optional): Whether to show warnings. Defaults to True.
            serialize_as_any (bool, optional): Whether to serialize as Any. Defaults to False.

        Returns:
            dict[str, Any]: The serialized model as a dictionary.
        """
    async def amodel_dump(self, *, mode: Literal['json', 'python'] | str = 'python', include: IncEx = None, exclude: IncEx = None, context: Any | None = None, by_alias: bool = False, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False, round_trip: bool = False, warnings: bool = True, serialize_as_any: bool = False) -> dict[str, Any]: ...
    @classmethod
    async def _async_model_dump(cls, obj: Any) -> Any: ...
    def model_dump_json_refs(self, *, indent: int | None = None, include: IncEx = None, exclude: IncEx = None, context: Any | None = None, by_alias: bool = False, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False, round_trip: bool = False, warnings: bool = True, serialize_as_any: bool = False) -> str:
        """
        Dumps the model as a JSON string with references.

        Args:
            indent (int | None, optional): The indentation of the JSON string. Defaults to None.
            include (IncEx, optional): Fields to include in the serialization. Defaults to None.
            exclude (IncEx, optional): Fields to exclude from the serialization. Defaults to None.
            context (Any | None, optional): The context of the serialization. Defaults to None.
            by_alias (bool, optional): Whether to use field aliases. Defaults to False.
            exclude_unset (bool, optional): Whether to exclude unset fields. Defaults to False.
            exclude_defaults (bool, optional): Whether to exclude fields with default values. Defaults to False.
            exclude_none (bool, optional): Whether to exclude fields with None values. Defaults to False.
            round_trip (bool, optional): Whether to ensure round-trip serialization. Defaults to False.
            warnings (bool, optional): Whether to show warnings. Defaults to True.
            serialize_as_any (bool, optional): Whether to serialize as Any. Defaults to False.

        Returns:
            str: The serialized model as a JSON string.
        """
    def model_dump_json(self, *, indent: int | None = None, include: IncEx = None, exclude: IncEx = None, context: Any | None = None, by_alias: bool = False, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False, round_trip: bool = False, warnings: bool = True, serialize_as_any: bool = False) -> str:
        """
        Dumps the model as a JSON string.

        Args:
            indent (int | None, optional): The indentation of the JSON string. Defaults to None.
            include (IncEx, optional): Fields to include in the serialization. Defaults to None.
            exclude (IncEx, optional): Fields to exclude from the serialization. Defaults to None.
            context (Any | None, optional): The context of the serialization. Defaults to None.
            by_alias (bool, optional): Whether to use field aliases. Defaults to False.
            exclude_unset (bool, optional): Whether to exclude unset fields. Defaults to False.
            exclude_defaults (bool, optional): Whether to exclude fields with default values. Defaults to False.
            exclude_none (bool, optional): Whether to exclude fields with None values. Defaults to False.
            round_trip (bool, optional): Whether to ensure round-trip serialization. Defaults to False.
            warnings (bool, optional): Whether to show warnings. Defaults to True.
            serialize_as_any (bool, optional): Whether to serialize as Any. Defaults to False.

        Returns:
            str: The serialized model as a JSON string.
        """
