from amsdal_models.classes.model import Model as Model
from amsdal_models.classes.relationships.constants import ANNOTATIONS as ANNOTATIONS, PRIMARY_KEY_FIELDS as PRIMARY_KEY_FIELDS
from amsdal_models.classes.relationships.reference_field import ReferenceFieldInfo as ReferenceFieldInfo
from pydantic.fields import FieldInfo as FieldInfo
from typing import Any, ForwardRef

def get_type_for(prop: str, bases: tuple[type[Any], ...], namespace: dict[str, Any]) -> type | str | ForwardRef: ...
def is_model_subclass(field_type: type) -> bool: ...
def is_forward_ref(target: Any) -> bool: ...
def is_forward_ref_or_model(target: Any) -> bool: ...
def resolve_model_type(annotation: Any) -> tuple[type['Model'] | ForwardRef | str, bool]:
    """
    Resolves a model type annotation, returning a tuple of the resolved model type and a boolean
    indicating whether it is it required.

    Arguments:
        annotation (Any): the model's field type annotation
    """
def convert_models_in_dict_to_references(namespace: dict[str, Any]) -> None: ...
def process_model_annotation(_annotation: Any) -> Any: ...
