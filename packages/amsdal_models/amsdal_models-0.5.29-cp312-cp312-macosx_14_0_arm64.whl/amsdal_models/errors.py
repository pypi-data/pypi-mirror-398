from amsdal_utils.errors import AmsdalError


class AmsdalValidationError(AmsdalError):
    def __init__(self, message: str) -> None:
        self.message = message


class MigrationsError(AmsdalError): ...


class AmsdalTypeError(AmsdalError):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AmsdalModelError(AmsdalError):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
