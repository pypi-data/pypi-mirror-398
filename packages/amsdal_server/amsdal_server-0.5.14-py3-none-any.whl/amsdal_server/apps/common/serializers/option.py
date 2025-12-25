from pydantic import BaseModel


class Option(BaseModel):
    key: str
    value: str
