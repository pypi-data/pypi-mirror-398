from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.models.data_models.reference import ReferenceData
from amsdal_utils.models.enums import Versions

from amsdal_models.storage.base import Storage


def build_storage_address(storage: Storage, name: str) -> Reference:
    """
    Build a Reference for a stored file according to the design contract.

    reference.ref fields:
    - resource: full Python path to the Storage class
    - class_name: "FileStorage"
    - class_version/object_version: Versions.LATEST
    - object_id: storage-specific locator (name/key/path)
    """
    storage_cls = storage.__class__
    resource = f'{storage_cls.__module__}.{storage_cls.__name__}'
    ref = ReferenceData(
        resource=resource,
        class_name='FileStorage',
        class_version=Versions.LATEST,
        object_id=name,
        object_version=Versions.LATEST,
    )
    return Reference(ref=ref)
