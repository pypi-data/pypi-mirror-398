from typing import Any


def validate_non_empty_keys(value: Any) -> Any:
    """
    Validates that dictionary keys are non-empty.

    Args:
        value (Any): The dictionary to validate.

    Returns:
        Any: The original dictionary if validation passes.

    Raises:
        ValueError: If any dictionary key is empty.
    """
    if value is None:
        return value

    for k in value:
        if len(k) == 0:
            msg = 'Dictionary keys must be non-empty'
            raise ValueError(msg)

    return value
