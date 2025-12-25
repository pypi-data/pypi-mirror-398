from fastapi import status
from fastapi.responses import JSONResponse

from amsdal_server.apps.healthcheck.enums import StatusEnum
from amsdal_server.apps.healthcheck.router import router
from amsdal_server.apps.healthcheck.services.checkers.connections import ConnectionsHealthchecker
from amsdal_server.apps.healthcheck.services.healthcheck import HealthcheckService

healthchecker = HealthcheckService(conditions=[ConnectionsHealthchecker()])


@router.get('/api/probes/liveness/')
async def liveness_probe() -> JSONResponse:
    result = await healthchecker.healthcheck()
    return JSONResponse(
        status_code=status.HTTP_200_OK if result.status == StatusEnum.success else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=result.model_dump(),
    )
