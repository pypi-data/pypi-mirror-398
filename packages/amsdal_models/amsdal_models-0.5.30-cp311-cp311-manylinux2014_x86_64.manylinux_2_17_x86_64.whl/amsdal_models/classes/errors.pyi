from _typeshed import Incomplete
from amsdal_utils.errors import AmsdalError
from amsdal_utils.models.data_models.address import Address as Address
from amsdal_utils.models.enums import ModuleType as ModuleType

class AmsdalUniquenessError(AmsdalError): ...

class ObjectAlreadyExistsError(AmsdalError):
    address: Incomplete
    def __init__(self, address: Address) -> None: ...

class AmsdalRecursionError(AmsdalError): ...
class AmsdalClassError(AmsdalError): ...

class AmsdalClassNotFoundError(AmsdalClassError):
    model_name: Incomplete
    module_type: Incomplete
    def __init__(self, model_name: str, module_type: ModuleType) -> None: ...
