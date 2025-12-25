from amsdal_utils.errors import AmsdalError

class AmsdalQuerySetError(AmsdalError):
    """Base class for all queryset errors"""
class ObjectDoesNotExistError(AmsdalQuerySetError):
    """The requested object does not exist"""
class MultipleObjectsReturnedError(AmsdalQuerySetError):
    """The query returned multiple objects when only one was expected."""
class BulkOperationError(AmsdalQuerySetError):
    """Error occurred during a bulk operation."""
