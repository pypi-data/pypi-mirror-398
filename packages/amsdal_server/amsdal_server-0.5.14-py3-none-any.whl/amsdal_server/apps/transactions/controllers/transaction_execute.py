from typing import Any

from fastapi import Body

from amsdal_server.apps.transactions.router import router
from amsdal_server.apps.transactions.services.transaction_execution_api import TransactionExecutionApi


@router.post('/api/transactions/{transaction_name}/')
async def transaction_execute(
    transaction_name: str,
    args: dict[Any, Any] = Body(...),
) -> Any:
    return await TransactionExecutionApi.execute_transaction(transaction_name, args)
