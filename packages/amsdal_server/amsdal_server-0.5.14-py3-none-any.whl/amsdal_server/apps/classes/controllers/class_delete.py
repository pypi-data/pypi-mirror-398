from fastapi import Request
from fastapi import status

from amsdal_server.apps.classes.router import router
from amsdal_server.apps.classes.services.classes_api import ClassesApi


@router.delete(
    '/api/classes/{class_name}/',
    status_code=status.HTTP_204_NO_CONTENT,
    description='Delete a class.',
)
async def class_delete(
    request: Request,
    class_name: str,
) -> None:
    ClassesApi.unregister_class(request.user, class_name)
