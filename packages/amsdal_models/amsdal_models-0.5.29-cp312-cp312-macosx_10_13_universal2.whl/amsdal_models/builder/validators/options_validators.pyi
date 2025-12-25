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
