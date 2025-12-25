import urllib.parse

from fastapi import Request
from fastapi import status

from amsdal_server.apps.objects.router import router
from amsdal_server.apps.objects.services.object_api import ObjectApi
from amsdal_server.apps.objects.utils import normalize_address


@router.delete('/api/objects/{address:path}/', status_code=status.HTTP_204_NO_CONTENT)
async def object_delete(
    request: Request,
    address: str,
) -> None:
    await ObjectApi.delete_object(
        request.user,
        address=normalize_address(urllib.parse.unquote(address)),
    )
