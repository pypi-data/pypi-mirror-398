from _typeshed import Incomplete
from pathlib import Path

reference_schema: Incomplete

def contrib_to_module_root_path(contrib: str) -> Path:
    """
    Converts a contrib string to the root path of the module.

    Args:
        contrib (str): The contrib string to convert.

    Returns:
        Path: The root path of the module.
    """
def build_migrations_module_name(package_module: str | None, migrations_directory_name: str) -> str:
    '''
    Builds the name of the migrations module.
    The package_module is None for apps migrations.
    The package_module is "amsdal" for core migrations.

    Args:
        package_module: Package module, e.g. "amsdal.contrib.auth"
        migrations_directory_name: The name of the migrations directory, e.g. "__migrations__".

    Returns:
        The module name that is concatenated with the migrations directory name.
    '''
def module_name_to_migrations_path(module_name: str) -> Path: ...
