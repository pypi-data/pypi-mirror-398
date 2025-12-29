from click import ClickException


class CraftLetException(ClickException):
    def __init__(self, errorMessage: str):
        super().__init__(message=errorMessage)
