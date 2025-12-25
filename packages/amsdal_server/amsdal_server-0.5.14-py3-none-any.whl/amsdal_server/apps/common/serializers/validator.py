from typing import Any

from amsdal_server.apps.common.serializers.base_serializer import SkipNoneBaseModel


class Validator(SkipNoneBaseModel):
    name: str
    data: Any
