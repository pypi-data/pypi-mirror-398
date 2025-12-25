from typing import Any

from fastapi import Body

from amsdal_server.apps.objects.router import router
from amsdal_server.apps.objects.services.object_api import ObjectApi


@router.post('/api/objects/{address:path}/validate/', status_code=204)
async def object_validate(
    class_name: str,
    data: dict[str, Any] = Body(...),
) -> None:
    ObjectApi.validate_object(
        class_name=class_name,
        data=data,
    )
