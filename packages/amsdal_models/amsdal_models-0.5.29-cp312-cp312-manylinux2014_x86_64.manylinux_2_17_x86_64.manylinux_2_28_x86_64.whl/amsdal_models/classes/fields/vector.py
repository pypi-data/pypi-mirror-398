from typing import Annotated

from pydantic import Field


def VectorField(dimensions: int):  # type: ignore  # noqa: N802
    """Create a type-safe, schema-aware VectorField."""
    return Annotated[
        list[float],
        Field(json_schema_extra={'dimensions': dimensions, 'additional_type': 'vector'}),
    ]
