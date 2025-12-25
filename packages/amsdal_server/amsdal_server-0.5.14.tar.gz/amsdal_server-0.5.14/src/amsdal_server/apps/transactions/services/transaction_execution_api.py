import base64
from typing import Any

from amsdal.services.transaction_execution import TransactionExecutionService
from amsdal_utils.config.manager import AmsdalConfigManager

from amsdal_server.apps.common.errors import AmsdalTransactionError


class TransactionExecutionApi:
    @classmethod
    async def execute_transaction(
        cls,
        transaction_name: str,
        args: dict[Any, Any],
    ) -> Any:
        execution_service = TransactionExecutionService()

        try:
            if AmsdalConfigManager().get_config().async_mode:
                res = await execution_service.async_execute_transaction(
                    transaction_name=transaction_name,
                    args=cls._decode_bytes(args),
                    load_references=True,
                )
            else:
                res = execution_service.execute_transaction(
                    transaction_name=transaction_name,
                    args=cls._decode_bytes(args),
                    load_references=True,
                )
            return cls._encode_bytes(res)
        except TypeError as e:
            msg = str(f'Invalid arguments: {e}')

            raise AmsdalTransactionError(transaction_name=transaction_name, error_message=msg) from e

    @classmethod
    def _decode_bytes(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {key: cls._decode_bytes(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [cls._decode_bytes(item) for item in data]
        elif isinstance(data, str) and data.startswith('data:binary;base64, '):
            return base64.b64decode(data.replace('data:binary;base64, ', '').encode('utf-8'))
        return data

    @classmethod
    def _encode_bytes(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {key: cls._encode_bytes(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [cls._encode_bytes(item) for item in data]
        elif isinstance(data, bytes | bytearray):
            return f'data:binary;base64, {base64.b64encode(data).decode("utf-8")}'
        return data
