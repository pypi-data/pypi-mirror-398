from pydantic import Field

from amsdal_server.apps.common.serializers.base_serializer import SkipNoneBaseModel
from amsdal_server.apps.common.serializers.column_response import ColumnInfo


class ClassInfo(SkipNoneBaseModel):
    class_name: str = Field(..., alias='class')
    properties: list[ColumnInfo]
    count: int = 0
