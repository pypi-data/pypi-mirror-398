from amsdal_models.classes.relationships.constants import FOREIGN_KEYS as FOREIGN_KEYS
from amsdal_models.classes.relationships.meta.references import build_fk_db_fields as build_fk_db_fields
from pydantic.functional_validators import ModelWrapValidatorHandler as ModelWrapValidatorHandler
from typing import Any, Self

def model_foreign_keys_validator(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self: ...
