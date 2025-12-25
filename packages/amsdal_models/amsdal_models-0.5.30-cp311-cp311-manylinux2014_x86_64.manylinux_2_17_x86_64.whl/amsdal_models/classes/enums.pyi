from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema
from enum import Enum

class CoreModules(str, Enum):
    """
    Enumeration for core modules.

    Attributes:
        REFERENCE (str): Represents the 'Reference' core module.
    """
    REFERENCE = 'Reference'

class SystemModules(str, Enum):
    """
    Enumeration for system modules.

    Attributes:
        DICT (str): Represents the 'dict' system module.
        LIST (str): Represents the 'list' system module.
        ANY (str): Represents the 'Any' system module.
        TYPE (str): Represents the 'type' system module.
        OPTIONAL (str): Represents the 'Optional' system module.
        UNION (str): Represents the 'Union' system module.
        CLASS_VAR (str): Represents the 'ClassVar' system module.
        FIELD_VALIDATOR (str): Represents the 'field_validator' system module.
        FIELD_DICTIONARY_VALIDATOR (str): Represents the 'validate_non_empty_keys' system module.
        FIELD_OPTIONS_VALIDATOR (str): Represents the 'validate_options' system module.
        DATE (str): Represents the 'date' system module.
        DATETIME (str): Represents the 'datetime' system module.
    """
    DICT = 'dict'
    LIST = 'list'
    ANY = 'Any'
    TYPE = 'type'
    OPTIONAL = 'Optional'
    UNION = 'Union'
    CLASS_VAR = 'ClassVar'
    FIELD_VALIDATOR = 'field_validator'
    FIELD_DICTIONARY_VALIDATOR = 'validate_non_empty_keys'
    FIELD_OPTIONS_VALIDATOR = 'validate_options'
    DATE = 'date'
    DATETIME = 'datetime'

class ModelType(str, Enum):
    """
    Enumeration for model types.

    Attributes:
        TYPE (str): Represents the 'type' model type.
        MODEL (str): Represents the 'model' model type.
    """
    TYPE = 'type'
    MODEL = 'model'
    @classmethod
    def from_schema(cls, schema: ObjectSchema) -> ModelType:
        """
        Determines the model type from the given schema.

        Args:
            schema (ObjectSchema): The schema to determine the model type from.

        Returns:
            ModelType: The determined model type.
        """
