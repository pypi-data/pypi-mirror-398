from amsdal_models.storage.base import Storage as Storage

def FileField(*args, storage: Storage | None = None, **kwargs):
    """Create a type-safe, schema-aware FileField."""
