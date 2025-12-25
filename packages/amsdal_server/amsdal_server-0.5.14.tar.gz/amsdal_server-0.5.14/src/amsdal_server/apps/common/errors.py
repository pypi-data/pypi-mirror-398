from amsdal_utils.errors import AmsdalError

from amsdal_server.apps.common.permissions.enums import AccessTypes


class AmsdalPermissionError(AmsdalError):
    def __init__(self, access_type: AccessTypes, class_name: str) -> None:
        self.access_type = access_type
        self.class_name = class_name


class AmsdalTransactionError(AmsdalError):
    def __init__(self, transaction_name: str, error_message: str) -> None:
        self.transaction_name = transaction_name
        self.error_message = error_message

    def __str__(self) -> str:
        return self.error_message
