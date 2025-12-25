from typing import Any


def validate_options(value: Any, options: list[Any]) -> Any:
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

    multi = isinstance(value, list)

    if (multi and isinstance(value, list) and all(v in options for v in value)) or (not multi and value in options):
        return value

    msg = f"Value={value} doesn't match available options: {options}."

    raise ValueError(msg)
