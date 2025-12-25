from collections.abc import Callable
from typing import Any
from typing import ClassVar

from amsdal_utils.schemas.schema import PropertyData

from amsdal_models.builder.validators.dict_validators import validate_non_empty_keys


class ValidatorResolver:
    TYPE_BASED_VALIDATORS: ClassVar[dict[str, Any]] = {
        'dictionary': (
            '_non_empty_keys_{FIELD_NAME}',
            validate_non_empty_keys,
        ),
    }

    @classmethod
    def process_property(
        cls,
        property_name: str,
        property_config: PropertyData,
    ) -> list[tuple[str, Callable[[Any, list[Any]], Any], list[Any] | None]]:
        """
        Processes a property and returns a list of validators.

        Args:
            property_name (str): The name of the property.
            property_config (PropertyData): The configuration of the property.

        Returns:
            list[tuple[str, Callable[[Any, list[Any]], Any], list[Any] | None]]: A list of validators.
        """
        _validators: list[tuple[str, Callable[[Any, list[Any]], Any], list[Any] | None]] = []
        field_type = property_config.type.lower()

        if field_type in cls.TYPE_BASED_VALIDATORS:
            field_name, validator = cls.TYPE_BASED_VALIDATORS[field_type]

            _validators.append(
                (
                    field_name.replace('{FIELD_NAME}', property_name.lower()),
                    validator,
                    None,
                ),
            )

        return _validators
