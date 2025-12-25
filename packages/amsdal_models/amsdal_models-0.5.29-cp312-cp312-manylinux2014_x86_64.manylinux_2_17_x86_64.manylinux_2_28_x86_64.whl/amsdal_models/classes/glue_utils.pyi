import amsdal_glue as glue
from amsdal_models.classes.handlers.reference_handler import EXCLUDE_M2M_FIELDS_FLAG as EXCLUDE_M2M_FIELDS_FLAG
from amsdal_models.classes.model import Model as Model
from amsdal_models.classes.relationships.constants import PRIMARY_KEY_FIELDS as PRIMARY_KEY_FIELDS

def model_to_data(obj: Model, *, exclude_m2m: bool = True) -> glue.Data:
    """
    Convert a model object to a data dictionary.

    Args:
        obj (Model): The model object to convert.
        exclude_m2m (bool, optional): Whether to exclude many-to-many fields. Defaults to True.

    Returns:
        amsdal_glue.Data: The data.
    """
