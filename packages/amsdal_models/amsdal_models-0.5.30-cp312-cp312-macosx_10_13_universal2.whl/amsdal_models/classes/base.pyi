from amsdal_utils.models.base import ModelBase
from amsdal_utils.models.enums import ModuleType as ModuleType
from typing import ClassVar

class BaseModel(ModelBase):
    """
    Base model class that extends the ModelBase class.

    Attributes:
        __module_type__ (ClassVar[ModuleType]): The schema type of the model.
    """
    __module_type__: ClassVar[ModuleType]
