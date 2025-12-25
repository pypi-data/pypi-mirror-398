import importlib
from pathlib import Path

from amsdal_utils.models.data_models.table_schema import NestedSchemaModel

reference_schema = NestedSchemaModel(
    properties={
        'ref': NestedSchemaModel(
            properties={
                'resource': str,
                'class_name': str,
                'class_version': str,
                'object_id': str,
                'object_version': str,
            },
        ),
    },
)


def contrib_to_module_root_path(contrib: str) -> Path:
    """
    Converts a contrib string to the root path of the module.

    Args:
        contrib (str): The contrib string to convert.

    Returns:
        Path: The root path of the module.
    """
    if contrib.endswith('AppConfig'):
        contrib_root = '.'.join(contrib.split('.')[:-2])
        contrib_root_module = importlib.import_module(contrib_root)

        return Path(contrib_root_module.__path__[0])
    else:
        _module = importlib.import_module(contrib)
        return Path(_module.__path__[0]).parent


def build_migrations_module_name(package_module: str | None, migrations_directory_name: str) -> str:
    """
    Builds the name of the migrations module.
    The package_module is None for apps migrations.
    The package_module is "amsdal" for core migrations.

    Args:
        package_module: Package module, e.g. "amsdal.contrib.auth"
        migrations_directory_name: The name of the migrations directory, e.g. "__migrations__".

    Returns:
        The module name that is concatenated with the migrations directory name.
    """

    if package_module is None:
        return migrations_directory_name

    return f'{package_module}.{migrations_directory_name}'


def module_name_to_migrations_path(module_name: str) -> Path:
    if '.' in module_name:
        module_path, migrations_directory_name = module_name.rsplit('.', 1)
        root_module = importlib.import_module(module_path)

        return Path(root_module.__path__[0]) / migrations_directory_name

    return Path('.') / module_name
