from amsdal_server.apps.common.serializers.base_serializer import SkipNoneBaseModel


class ColumnFormat(SkipNoneBaseModel):
    headerTemplate: str | None = None  # noqa: N815
    cellTemplate: str | None = None  # noqa: N815
