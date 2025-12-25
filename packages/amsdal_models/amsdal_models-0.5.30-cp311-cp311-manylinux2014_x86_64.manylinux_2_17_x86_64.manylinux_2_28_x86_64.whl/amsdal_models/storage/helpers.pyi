from amsdal_models.storage.base import Storage as Storage
from amsdal_utils.models.data_models.reference import Reference

def build_storage_address(storage: Storage, name: str) -> Reference:
    '''
    Build a Reference for a stored file according to the design contract.

    reference.ref fields:
    - resource: full Python path to the Storage class
    - class_name: "FileStorage"
    - class_version/object_version: Versions.LATEST
    - object_id: storage-specific locator (name/key/path)
    '''
