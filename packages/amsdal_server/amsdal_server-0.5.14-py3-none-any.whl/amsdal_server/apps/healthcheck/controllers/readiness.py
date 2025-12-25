from fastapi import status
from fastapi.responses import JSONResponse

from amsdal_server.apps.healthcheck.router import router


@router.get('/api/probes/readiness/')
async def readiness_probe() -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_200_OK, content={})
