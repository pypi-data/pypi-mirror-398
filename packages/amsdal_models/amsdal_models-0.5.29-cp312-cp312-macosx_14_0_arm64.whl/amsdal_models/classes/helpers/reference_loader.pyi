from _typeshed import Incomplete
from amsdal_models.classes.class_manager import ClassManager as ClassManager
from amsdal_models.classes.model import Model as Model
from amsdal_models.querysets.base_queryset import QuerySetOneRequired as QuerySetOneRequired
from amsdal_utils.models.data_models.reference import Reference as Reference, ReferenceLoaderBase

class ReferenceLoader(ReferenceLoaderBase):
    _reference: Incomplete
    def __init__(self, reference: Reference) -> None: ...
    def load_reference(self, only: list[str] | None = None, using: str | None = None) -> Model:
        """
        Loads a reference.

        Args:
            only (list[str] | None, optional): Fields to include in the loaded reference. Defaults to None.
            using (str | None, optional): The database alias to use. Defaults to None.

        Returns:
            Model: The loaded model.
        """
    async def aload_reference(self, only: list[str] | None = None, using: str | None = None) -> Model:
        """
        Loads a reference asynchronously.

        Args:
            only (list[str] | None, optional): Fields to include in the loaded reference. Defaults to None.
            using (str | None, optional): The database alias to use. Defaults to None.

        Returns:
            Model: The loaded model.
        """
    def _load_model_class(self) -> type[Model]: ...
    def _load_record(self, model_class: type[Model], only: list[str] | None = None, using: str | None = None) -> QuerySetOneRequired[Model]: ...
