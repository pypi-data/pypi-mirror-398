from typing import Literal

from pydantic import BaseModel

from amsdal_server.apps.transactions.serializers.transaction_property import TransactionPropertySerializer


class TransactionItemSerializer(BaseModel):
    title: str
    type: Literal['Transaction'] = 'Transaction'
    properties: dict[str, TransactionPropertySerializer]
