import abc
from abc import ABC, abstractmethod
from amsdal_models.builder.class_source_builder import ClassSourceBuilder as ClassSourceBuilder
from amsdal_models.builder.utils import ModelModuleInfo as ModelModuleInfo
from amsdal_models.classes.model import Model as Model
from amsdal_utils.models.enums import ModuleType as ModuleType, Versions
from amsdal_utils.schemas.schema import ObjectSchema as ObjectSchema
from typing import Any

class BaseMigrationSchemas(ABC, metaclass=abc.ABCMeta):
    """
    Abstract base class for migration schemas.

    This class provides the interface for managing and compiling database schema migrations.
    It includes methods for registering, unregistering, and compiling classes, as well as
    managing class versions.
    """
    _classes: dict[str, type[Model]]
    _classes_versions: dict[str, dict[str, type[Model]]]
    _buffered_classes: list[tuple[str, ObjectSchema, ModuleType]]
    def __init__(self) -> None: ...
    @property
    def classes_namespace(self) -> dict[str, type[Model]]: ...
    def get_model(self, name: str) -> type[Model]:
        """
        Retrieves the model type for the given class name.

        Args:
            name (str): The name of the class whose model type is to be retrieved.

        Returns:
            type[Model]: The model type associated with the given class name.
        """
    def registered_model_names(self) -> list[str]:
        """
        Returns a list of registered model names.
        This method retrieves the names of all registered model classes.
        It filters the classes to include only those that are subclasses of the Model class.

        Returns:
            list[str]: A list of registered model names.
        """
    @abstractmethod
    def register_model(self, class_name: str, object_schema: ObjectSchema, module_type: ModuleType, class_version: str | Versions = ...) -> None: ...
    @abstractmethod
    def unregister_model(self, class_name: str) -> None: ...
    @abstractmethod
    def compile_buffered_classes(self) -> None: ...
    @abstractmethod
    def compile_classes(self, class_schemas: list[tuple[str, ObjectSchema, ModuleType]], namespace: dict[str, Any]) -> list[tuple[str, type[Model]]]: ...
    @staticmethod
    def register_model_version(class_name: str, class_version: str | Versions) -> None:
        """
        Registers a specific version of a model class.

        This method registers a specific version of a model class using the ClassVersionManager.

        Args:
            class_name (str): The name of the class to register the version for.
            class_version (str | Versions): The version of the class to be registered.

        Returns:
            None
        """

class DefaultMigrationSchemas(BaseMigrationSchemas):
    """
    Default implementation of the BaseMigrationSchemas.

    This class provides the default implementation for managing and compiling database schema migrations.
    It includes methods for registering, unregistering, and compiling classes, as well as managing class versions.
    """
    def register_model(self, class_name: str, object_schema: ObjectSchema, module_type: ModuleType, class_version: str | Versions = ...) -> None:
        """
        Registers a model class for migration.

        This method registers a model class for migration by adding it to the buffered classes
        and registering its latest version.

        Args:
            class_name (str): The name of the class to be registered.
            object_schema (ObjectSchema): The schema of the object to be registered.
            module_type (SchemaTypes): The type of the schema.

        Returns:
            None
        """
    def compile_buffered_classes(self) -> None:
        """
        Compiles all buffered classes for migration.

        This method compiles all classes that have been buffered for migration and updates the
        internal class dictionary with the compiled class types. It clears the buffer after
        compilation.

        Returns:
            None
        """
    def unregister_model(self, class_name: str) -> None:
        """
        Unregisters a model class from the migration schemas.

        This method removes the specified model class from the internal class dictionary,
        effectively unregistering it from the migration schemas.

        Args:
            class_name (str): The name of the class to be unregistered.

        Returns:
            None
        """
    def compile_classes(self, class_schemas: list[tuple[str, ObjectSchema, ModuleType]], namespace: dict[str, Any]) -> list[tuple[str, type[Model]]]: ...
    @staticmethod
    def _sort_schemas(class_schemas: list[tuple[str, ObjectSchema, ModuleType]]) -> list[tuple[str, ObjectSchema, ModuleType]]: ...
    @staticmethod
    def _resolve_class_inheritance(schema: ObjectSchema) -> type | str: ...
