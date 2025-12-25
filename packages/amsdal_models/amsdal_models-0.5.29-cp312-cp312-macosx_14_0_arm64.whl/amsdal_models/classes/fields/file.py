from pydantic import Field

from amsdal_models.storage.base import Storage


def FileField(*args, storage: Storage | None = None, **kwargs):  # type: ignore  # noqa: N802
    """Create a type-safe, schema-aware FileField."""
    return Field(
        *args,
        json_schema_extra=storage.to_storage_spec() if storage else {},
        **kwargs,
    )
