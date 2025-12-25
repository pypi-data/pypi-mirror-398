from amsdal_models.classes.model import AmsdalModelMetaclass as AmsdalModelMetaclass, Model as Model
from amsdal_models.classes.relationships.constants import DEFERRED_M2M_FIELDS as DEFERRED_M2M_FIELDS, MANY_TO_MANY_FIELDS as MANY_TO_MANY_FIELDS
from amsdal_models.classes.relationships.meta.common import is_forward_ref as is_forward_ref, is_model_subclass as is_model_subclass
from amsdal_models.classes.relationships.meta.many_to_many import build_m2m_model as build_m2m_model, generate_dynamic_m2m_fields as generate_dynamic_m2m_fields, resolve_m2m_ref as resolve_m2m_ref
from typing import Any

def complete_deferred_many_to_many(cls, _types_namespace: dict[str, Any] | None = None) -> bool:
    """
    Complete the deferred many-to-many fields on the model.
    Args:
        cls: Model class to complete deferred many-to-many fields on.

    Returns:
        bool: True if all deferred many-to-many fields were resolved, False otherwise.

    """
