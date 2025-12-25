from typing import Any

from fastapi import Body
from fastapi import Request
from fastapi import status

from amsdal_server.apps.objects.router import router
from amsdal_server.apps.objects.services.object_api import ObjectApi


@router.post('/api/objects/', status_code=status.HTTP_201_CREATED)
async def object_create(
    request: Request,
    class_name: str,
    *,
    load_references: bool = False,
    data: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    return await ObjectApi.create_object(
        request.user,
        base_url=str(request.base_url),
        class_name=class_name,
        data=data,
        load_references=load_references,
    )
