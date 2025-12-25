from amsdal_models.classes.base import BaseModel as BaseModel
from amsdal_models.classes.constants import CONTRIB_MODELS_MODULE as CONTRIB_MODELS_MODULE, CORE_MODELS_MODULE as CORE_MODELS_MODULE, TYPE_MODELS_MODULE as TYPE_MODELS_MODULE, USER_MODELS_MODULE as USER_MODELS_MODULE
from amsdal_models.classes.decorators.private_property import PrivateProperty as PrivateProperty
from amsdal_models.classes.model import Model as Model, TypeModel as TypeModel
from amsdal_utils.models.base import ModelBase
from amsdal_utils.models.data_models.reference import Reference as Reference
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema
from typing import Any

def resolve_models_module(models_module_name: str, module_type: ModuleType) -> str:
    """
    Resolves the module name for the given schema type.

    Args:
        models_module_name (str): The base name of the models module.
        module_type (ModuleType): The type of schema to resolve the module for.

    Returns:
        str: The resolved module name.

    Raises:
        ValueError: If the schema type is invalid.
    """
def resolve_base_class_for_schema(schema: ObjectSchema) -> type[Model | TypeModel]:
    """
    Resolves the base class for the given schema.

    Args:
        schema (ObjectSchema): The schema to resolve the base class for.

    Returns:
        type[Union['Model', 'TypeModel']]: The resolved base class.

    Raises:
        ValueError: If the schema's meta class is invalid.
    """
def build_class_schema_reference(class_name: str, model_class: type[BaseModel]) -> Reference:
    """
    Builds a reference to the class schema for the given model class.

    Args:
        class_name (str): The name of the class to build the schema reference for.
        model_class (type[BaseModel]): The model class to build the schema reference for.

    Returns:
        Reference: The reference to the class schema.

    Raises:
        ValueError: If the schema type is invalid.
    """
def build_class_meta_schema_reference(class_name: str, object_id: Any) -> Reference | None:
    """
    Builds a reference to the class meta schema for the given model class and object ID.

    Args:
        class_name (str): The name of the class to build the meta schema reference for.
        object_id (Any): The object ID to build the meta schema reference for.

    Returns:
        Reference | None: The reference to the class meta schema, or None if the model class is not CLASS_OBJECT_META.
    """
def get_custom_properties(model: type[ModelBase]) -> set[str]:
    """
    Retrieves custom properties from the given model class.

    This function iterates through the method resolution order (MRO) of the model class and collects all properties
    that are not instances of PrivateProperty.

    Args:
        model (type[ModelBase]): The model class to retrieve custom properties from.

    Returns:
        set[str]: A set of custom property names.
    """
def is_partial_model(model_class: type[Any]) -> bool:
    """
    Checks if the given model class is a partial model.

    Args:
        model_class (type[Any]): The model class to check.

    Returns:
        bool: True if the model class is a partial model, False otherwise.
    """
def object_id_to_internal(object_id: Any) -> Any: ...
