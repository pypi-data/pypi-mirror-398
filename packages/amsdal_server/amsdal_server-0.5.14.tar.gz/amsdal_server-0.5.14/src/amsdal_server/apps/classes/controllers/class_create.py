from fastapi import Request

from amsdal_server.apps.classes.router import router
from amsdal_server.apps.classes.serializers.class_info import ClassInfo
from amsdal_server.apps.classes.serializers.register_class import RegisterClassData
from amsdal_server.apps.classes.services.classes_api import ClassesApi


@router.post('/api/classes/', description='Register a class.')
async def class_create(
    request: Request,
    data: RegisterClassData,
    *,
    skip_data_migrations: bool = False,
) -> ClassInfo:
    return ClassesApi.register_class(request.user, data, skip_data_migrations=skip_data_migrations)
