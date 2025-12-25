from amsdal_models.classes.decorators.private_property import PrivateProperty as PrivateProperty
from amsdal_models.classes.model import AmsdalModelMetaclass as AmsdalModelMetaclass, Model as Model
from amsdal_models.classes.relationships.constants import DEFERRED_FOREIGN_KEYS as DEFERRED_FOREIGN_KEYS, FOREIGN_KEYS as FOREIGN_KEYS, PRIMARY_KEY_FIELDS as PRIMARY_KEY_FIELDS
from amsdal_models.classes.relationships.meta.common import is_forward_ref as is_forward_ref, is_model_subclass as is_model_subclass, resolve_model_type as resolve_model_type
from amsdal_models.classes.relationships.reference_field import ReferenceFieldInfo as ReferenceFieldInfo

def complete_deferred_foreign_keys(cls) -> None: ...
