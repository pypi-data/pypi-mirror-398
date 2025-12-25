import urllib.parse
from typing import Any

from fastapi import Body
from fastapi import Request

from amsdal_server.apps.objects.router import router
from amsdal_server.apps.objects.services.object_api import ObjectApi
from amsdal_server.apps.objects.utils import normalize_address


@router.post('/api/objects/{address:path}/')
@router.put('/api/objects/{address:path}/')
async def object_update(
    request: Request,
    address: str,
    *,
    data: dict[str, Any] = Body(...),
    load_references: bool = False,
) -> Any:
    return await ObjectApi.update_object(
        request.user,
        base_url=str(request.base_url),
        address=normalize_address(urllib.parse.unquote(address)),
        data=data,
        load_references=load_references,
    )


@router.patch('/api/objects/{address:path}/')
async def object_partial_update(
    request: Request,
    address: str,
    *,
    data: dict[str, Any] = Body(...),
    load_references: bool = False,
) -> Any:
    return await ObjectApi.partial_update_object(
        request.user,
        base_url=str(request.base_url),
        address=normalize_address(urllib.parse.unquote(address)),
        data=data,
        load_references=load_references,
    )
