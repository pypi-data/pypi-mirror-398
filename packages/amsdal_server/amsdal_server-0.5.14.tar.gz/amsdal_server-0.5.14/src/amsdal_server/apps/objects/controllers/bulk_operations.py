from typing import Any

from fastapi import Body
from fastapi import Request
from fastapi import status

from amsdal_server.apps.objects.router import router
from amsdal_server.apps.objects.services.object_api import BulkAddressBody
from amsdal_server.apps.objects.services.object_api import BulkUpdateBody
from amsdal_server.apps.objects.services.object_api import ObjectApi


@router.post('/api/objects/bulk-create/', status_code=status.HTTP_201_CREATED)
async def object_bulk_create(
    request: Request,
    class_name: str,
    *,
    load_references: bool = False,
    data: list[dict[str, Any]] = Body(...),
) -> list[dict[str, Any]]:
    return await ObjectApi.bulk_create_objects(
        request.user,
        base_url=str(request.base_url),
        class_name=class_name,
        data=data,
        load_references=load_references,
    )


@router.post('/api/objects/bulk-update/')
@router.put('/api/objects/bulk-update/')
async def object_bulk_update(
    request: Request,
    *,
    data: list[BulkUpdateBody] = Body(...),
    load_references: bool = False,
) -> Any:
    return await ObjectApi.bulk_update_objects(
        request.user,
        base_url=str(request.base_url),
        data=data,
        load_references=load_references,
    )


@router.patch('/api/objects/bulk-update/')
async def object_bulk_partial_update(
    request: Request,
    *,
    data: list[BulkUpdateBody] = Body(...),
    load_references: bool = False,
) -> Any:
    return await ObjectApi.bulk_partial_update_objects(
        request.user,
        base_url=str(request.base_url),
        data=data,
        load_references=load_references,
    )


@router.post('/api/objects/bulk-delete/', status_code=status.HTTP_204_NO_CONTENT)
async def object_bulk_delete(
    request: Request,
    *,
    data: list[BulkAddressBody] = Body(...),
) -> None:
    await ObjectApi.bulk_delete_objects(request.user, data=data)
