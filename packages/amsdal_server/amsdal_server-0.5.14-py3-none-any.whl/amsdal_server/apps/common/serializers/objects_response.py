from typing import Any

from amsdal_server.apps.common.serializers.base_serializer import SkipNoneBaseModel
from amsdal_server.apps.common.serializers.column_response import ColumnInfo


class ObjectsResponse(SkipNoneBaseModel):
    columns: list[ColumnInfo]
    rows: list[Any]
    total: int


class ObjectsResponseControl(SkipNoneBaseModel):
    columns: list[ColumnInfo]
    rows: list[Any]
    control: dict[str, Any]
