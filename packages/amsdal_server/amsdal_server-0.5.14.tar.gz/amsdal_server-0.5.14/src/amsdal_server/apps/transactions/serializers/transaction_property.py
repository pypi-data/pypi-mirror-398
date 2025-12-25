from pydantic import BaseModel


class TypeSerializer(BaseModel):
    type: str


class DictTypeSerializer(BaseModel):
    key: TypeSerializer
    value: TypeSerializer


class TransactionPropertySerializer(BaseModel):
    title: str
    type: str = 'string'
    items: DictTypeSerializer | TypeSerializer | None = None
