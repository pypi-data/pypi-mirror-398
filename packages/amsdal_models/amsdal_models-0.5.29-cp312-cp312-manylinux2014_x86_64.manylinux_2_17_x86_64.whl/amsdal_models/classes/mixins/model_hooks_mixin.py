from typing import Any


class ModelHooksMixin:
    def pre_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:
        """
        This hook is called just before the model is initialized and the built-in validations are executed.
        This hook is useful for setting default values for the model fields or for validating the keyword arguments.

        Args:
            is_new_object (bool): Indicates if the model is being initialized as a new record or existing one.
            kwargs (dict[str, Any]): Dictionary of keyword arguments passed to the model constructor.

        Returns:
            None: Does not return anything.
        """
        pass

    def post_init(self, *, is_new_object: bool, kwargs: dict[str, Any]) -> None:
        """
        This hook is called just after the model is initialized and the built-in validations are executed.
        This hook also is useful for setting default values for the model fields or for extra validating the keyword
        arguments.

        Args:
            is_new_object (bool): Indicates if the model is being initialized as a new record or existing one.
            kwargs (dict[str, Any]): Dictionary of keyword arguments passed to the model constructor.

        Returns:
            None: Does not return anything.
        """
        pass

    def pre_create(self) -> None:
        """
        This hook is called just before the new record of the model is saved to the database.
        It doesn't accept any arguments.
        This hook is useful for setting default values for the model fields or for validating the model before
        saving it to the database.
        At this stage, the object is not saved to the database yet.

        Returns:
            None: Does not return anything.
        """
        pass

    async def apre_create(self) -> None:
        """
        This hook is called just before the new record of the model is saved to the database.
        It doesn't accept any arguments.
        This hook is useful for setting default values for the model fields or for validating the model before
        saving it to the database.
        At this stage, the object is not saved to the database yet.

        Returns:
            None: Does not return anything.
        """
        pass

    def post_create(self) -> None:
        """
        This hook is called just after the new record of the model is saved to the database.
        It doesn't accept any arguments.
        This hook is useful for adding extra logic after the model is saved to the database.
        For example, you can send a notification to the user that the new record is created.
        At this stage, the object is already saved to the database and can be referenced by other records.

        Returns:
            None: Does not return anything.
        """

    async def apost_create(self) -> None:
        """
        This hook is called just after the new record of the model is saved to the database.
        It doesn't accept any arguments.
        This hook is useful for adding extra logic after the model is saved to the database.
        For example, you can send a notification to the user that the new record is created.
        At this stage, the object is already saved to the database and can be referenced by other records.

        Returns:
            None: Does not return anything.
        """

    def pre_update(self) -> None:
        """
        This hook is called just before the existing record of the model is updated in the database.
        It doesn't accept any arguments.
        This hook is useful for validating the model before updating it in the database.
        At this stage, the object is not updated in the database yet, so previous_version may return None.

        Returns:
            None: Does not return anything.
        """
        pass

    async def apre_update(self) -> None:
        """
        This hook is called just before the existing record of the model is updated in the database.
        It doesn't accept any arguments.
        This hook is useful for validating the model before updating it in the database.
        At this stage, the object is not updated in the database yet, so previous_version may return None.

        Returns:
            None: Does not return anything.
        """
        pass

    def post_update(self) -> None:
        """
        This hook is called just after the existing record of the model is updated in the database.
        It doesn't accept any arguments.
        This hook is useful for adding extra logic after the model is updated in the database.
        For example, you can send a notification to the user that the record is updated.
        At this stage, the object is already updated in the database, and calling previous_version will return the
        version of the object before the update.

        Returns:
            None: Does not return anything.
        """
        pass

    async def apost_update(self) -> None:
        """
        This hook is called just after the existing record of the model is updated in the database.
        It doesn't accept any arguments.
        This hook is useful for adding extra logic after the model is updated in the database.
        For example, you can send a notification to the user that the record is updated.
        At this stage, the object is already updated in the database, and calling previous_version will return the
        version of the object before the update.

        Returns:
            None: Does not return anything.
        """
        pass

    def pre_delete(self) -> None:
        """
        This hook is called just before the existing record of the model is deleted from the database.
        It doesn't accept any arguments.
        This hook is useful for validating the model before deleting it from the database.
        At this stage, the object is not deleted from the database yet.

        Returns:
            None: Does not return anything.
        """
        pass

    async def apre_delete(self) -> None:
        """
        This hook is called just before the existing record of the model is deleted from the database.
        It doesn't accept any arguments.
        This hook is useful for validating the model before deleting it from the database.
        At this stage, the object is not deleted from the database yet.

        Returns:
            None: Does not return anything.
        """
        pass

    def post_delete(self) -> None:
        """
        This hook is called just after the existing record of the model is deleted from the database.
        It doesn't accept any arguments.
        This hook is useful for adding extra logic after the model is deleted from the database.
        For example, you can send a notification to the user that the record is deleted.

        Returns:
            None: Does not return anything.
        """
        pass

    async def apost_delete(self) -> None:
        """
        This hook is called just after the existing record of the model is deleted from the database.
        It doesn't accept any arguments.
        This hook is useful for adding extra logic after the model is deleted from the database.
        For example, you can send a notification to the user that the record is deleted.

        Returns:
            None: Does not return anything.
        """
        pass
