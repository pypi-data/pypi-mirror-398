from amsdal_models.classes.model import AmsdalModelMetaclass as AmsdalModelMetaclass, Model as Model
from amsdal_models.classes.relationships.constants import DEFERRED_PRIMARY_KEYS as DEFERRED_PRIMARY_KEYS, PRIMARY_KEY_FIELDS as PRIMARY_KEY_FIELDS
from amsdal_models.classes.relationships.meta.common import is_forward_ref as is_forward_ref, resolve_model_type as resolve_model_type

def complete_deferred_primary_keys(cls) -> None: ...
