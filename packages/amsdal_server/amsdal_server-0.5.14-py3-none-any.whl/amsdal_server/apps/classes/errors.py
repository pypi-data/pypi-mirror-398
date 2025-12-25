from typing import Any

from amsdal_utils.errors import AmsdalError


class ClassNotFoundError(AmsdalError):
    def __init__(self, class_name: str, *args: Any) -> None:
        self.class_name = class_name

        if not args:
            args = (f'Class not found: {class_name}',)

        super().__init__(*args)


class TransactionNotFoundError(AmsdalError):
    def __init__(self, transaction_name: str, *args: Any) -> None:
        self.transaction_name = transaction_name
        super().__init__(*args)
