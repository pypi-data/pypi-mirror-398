import ast
import re
from typing import Any
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator


class DictItem(BaseModel):
    key: 'TypeSchema'
    value: 'TypeSchema'


class TypeSchema(BaseModel):
    type: str
    items: Optional[Union[DictItem, 'TypeSchema']] = None


class OptionSchema(BaseModel):
    key: str
    value: str


class PropertySchema(BaseModel):
    type: str
    default: Any = None
    title: str | None = None
    items: TypeSchema | DictItem | None = None
    options: list[OptionSchema] | None = None


class ClassSchema(BaseModel):
    title: str
    type: str = 'object'
    properties: dict[str, PropertySchema]
    required: list[str] = Field(default_factory=list)
    indexed: list[str] = Field(default_factory=list)
    unique: list[list[str]] = Field(default_factory=list)
    custom_code: str = ''

    @field_validator('title')
    @classmethod
    def validate_class_title(cls, v: str) -> str:
        title = v.strip()

        if not title:
            msg = 'The title property cannot be empty'
            raise ValueError(msg)

        pattern = r'^[A-Z][a-z]*([A-Z][a-z]*)*$'

        if not bool(re.match(pattern, title)):
            msg = 'The title property should be in PascalCase due to use it as a class name'
            raise ValueError(msg)

        return title

    @field_validator('custom_code')
    @classmethod
    def validate_custom_code(cls, v: str) -> str:
        if not v:
            return ''

        try:
            ast.parse(v)
        except SyntaxError as e:
            msg = 'The custom_code property contains invalid code'
            raise ValueError(msg) from e

        return v

    @model_validator(mode='after')
    def check_required(self) -> 'ClassSchema':
        missing_properties = [prop for prop in self.required if prop not in self.properties]

        if missing_properties:
            msg = f'The required property contains unknown properties: {missing_properties}'
            raise ValueError(msg)

        return self

    @model_validator(mode='after')
    def check_indexed(self) -> 'ClassSchema':
        missing_properties = [prop for prop in self.indexed if prop not in self.properties]

        if missing_properties:
            msg = f'The indexed property contains unknown properties: {missing_properties}'
            raise ValueError(msg)

        return self

    @model_validator(mode='after')
    def check_unique(self) -> 'ClassSchema':
        missing_properties = set()

        for props in self.unique:
            for prop in props:
                if prop not in self.properties:
                    missing_properties.add(prop)

        if missing_properties:
            msg = f'The unique property contains unknown properties: {missing_properties}'
            raise ValueError(msg)

        return self


class RegisterClassData(BaseModel):
    class_schema: ClassSchema


TypeSchema.model_rebuild()
DictItem.model_rebuild()
