from amsdal_models.builder.validators.dict_validators import validate_non_empty_keys as validate_non_empty_keys
from amsdal_utils.schemas.schema import PropertyData as PropertyData
from collections.abc import Callable as Callable
from typing import Any, ClassVar

class ValidatorResolver:
    TYPE_BASED_VALIDATORS: ClassVar[dict[str, Any]]
    @classmethod
    def process_property(cls, property_name: str, property_config: PropertyData) -> list[tuple[str, Callable[[Any, list[Any]], Any], list[Any] | None]]:
        """
        Processes a property and returns a list of validators.

        Args:
            property_name (str): The name of the property.
            property_config (PropertyData): The configuration of the property.

        Returns:
            list[tuple[str, Callable[[Any, list[Any]], Any], list[Any] | None]]: A list of validators.
        """
