from enum import Enum
from typing import Any
from typing import Optional

from pydantic import Field

from amsdal_server.apps.common.serializers.base_serializer import SkipNoneBaseModel
from amsdal_server.apps.common.serializers.column_format import ColumnFormat
from amsdal_server.apps.common.serializers.option import Option
from amsdal_server.apps.common.serializers.validator import Validator


class FieldFilterInputType(str, Enum):
    SINGLE_SELECT = 'single_select'
    SINGLE_SELECT2 = 'single_select2'
    MULTI_SELECT = 'multi_select'
    MULTI_SELECT2 = 'multi_select2'
    TEXT = 'text'
    DATE = 'date'
    DATE_TIME = 'dateTime'
    NUMBER = 'number'


class FieldFilterControl(SkipNoneBaseModel):
    key: str
    type: FieldFilterInputType
    label: str | None = None
    placeholder: str | None = None
    value: Any | None = None
    options: list[Any] | None = None


class FieldFilter(SkipNoneBaseModel):
    type: str
    control: FieldFilterControl


class ColumnFilter(SkipNoneBaseModel):
    name: str | None = None
    label: str | None = None
    tooltip: str | None = None
    filters: list[FieldFilter] | None = None


class ColumnInfo(SkipNoneBaseModel):
    type: str | None = None
    value: str | None = None
    key: str | None = None
    label: str | None = None
    description: str | None = None
    order: int | None = None
    options: list[Option] | None = None
    cell_template_name: str | None = Field(None, alias='cellTemplateName')
    control: dict[str, Any] | None = None
    validation: list[Validator] | None = None
    column_format: ColumnFormat | None = None
    items: dict[str, Any] | None = None
    next_control: str | None = None
    head_control: str | None = None
    read_only: bool | None = None
    required: bool | None = None
    attributes: list['ColumnInfo'] | None = None
    array_type: str | None = None
    dict_type: str | None = None
    item_format: Optional['ColumnInfo'] = None
    filters: ColumnFilter | None = None
