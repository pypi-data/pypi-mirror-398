from pydantic import BaseModel


class FieldsRestriction(BaseModel):
    class_name: str
    fields: list[str]
