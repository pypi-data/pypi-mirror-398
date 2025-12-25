import amsdal_glue as glue
from amsdal_models.classes.model import Model as Model
from amsdal_models.classes.relationships.constants import PRIMARY_KEY_FIELDS as PRIMARY_KEY_FIELDS

def build_pk_query(table_name: str, obj: Model) -> glue.Conditions: ...
