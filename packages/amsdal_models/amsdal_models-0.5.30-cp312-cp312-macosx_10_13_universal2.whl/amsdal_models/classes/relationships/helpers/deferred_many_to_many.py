from copy import deepcopy
from typing import TYPE_CHECKING
from typing import Any
from typing import ForwardRef
from typing import Union

from amsdal_models.classes.relationships.constants import DEFERRED_M2M_FIELDS
from amsdal_models.classes.relationships.constants import MANY_TO_MANY_FIELDS
from amsdal_models.classes.relationships.meta.common import is_forward_ref
from amsdal_models.classes.relationships.meta.common import is_model_subclass
from amsdal_models.classes.relationships.meta.many_to_many import build_m2m_model
from amsdal_models.classes.relationships.meta.many_to_many import generate_dynamic_m2m_fields
from amsdal_models.classes.relationships.meta.many_to_many import resolve_m2m_ref

if TYPE_CHECKING:
    from amsdal_models.classes.model import AmsdalModelMetaclass
    from amsdal_models.classes.model import Model


def complete_deferred_many_to_many(
    cls: Union[type['Model'], 'AmsdalModelMetaclass'],
    _types_namespace: dict[str, Any] | None = None,
) -> bool:
    """
    Complete the deferred many-to-many fields on the model.
    Args:
        cls: Model class to complete deferred many-to-many fields on.

    Returns:
        bool: True if all deferred many-to-many fields were resolved, False otherwise.

    """
    do_rebuild_model = False
    deferred_m2m: dict[str, ForwardRef] = getattr(cls, DEFERRED_M2M_FIELDS, {})

    if not deferred_m2m:
        return True

    setattr(cls, DEFERRED_M2M_FIELDS, {})

    for m2m, deferred_m2m_value in deferred_m2m.items():
        _annotation = cls.model_fields[m2m].annotation  # type: ignore[union-attr]
        m2m_ref, m2m_model, through_fields, _ = resolve_m2m_ref(_annotation)
        field_info = cls.model_fields[m2m]  # type: ignore[union-attr]

        if is_forward_ref(m2m_ref):
            getattr(cls, DEFERRED_M2M_FIELDS).update({m2m: deferred_m2m_value})
            continue

        if is_model_subclass(m2m_ref):  # type: ignore[arg-type]
            do_rebuild_model = True
            del cls.model_fields[m2m]  # type: ignore[union-attr]

            if not m2m_model:
                m2m_model = build_m2m_model(
                    cls,
                    to_model=m2m_ref,  # type: ignore[arg-type]
                )

            _m2m_fields = deepcopy(getattr(cls, MANY_TO_MANY_FIELDS, None) or {})
            _m2m_fields[m2m] = m2m_ref, m2m_model, through_fields, field_info
            setattr(cls, MANY_TO_MANY_FIELDS, _m2m_fields)
            generate_dynamic_m2m_fields(m2m, m2m_ref, m2m_model, through_fields, cls)  # type: ignore[arg-type]

    if do_rebuild_model:
        cls.model_rebuild(force=True, _types_namespace=_types_namespace)  # type: ignore[union-attr]

    return not bool(getattr(cls, DEFERRED_M2M_FIELDS))
