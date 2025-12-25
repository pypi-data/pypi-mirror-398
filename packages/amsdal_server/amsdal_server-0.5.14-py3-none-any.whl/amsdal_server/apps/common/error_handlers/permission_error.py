import logging

from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse

from amsdal_server.apps.common.errors import AmsdalPermissionError

logger = logging.getLogger(__name__)


async def permission_error_handler(
    request: Request,  # noqa: ARG001
    exc: AmsdalPermissionError,
) -> JSONResponse:
    logger.info('Permission error: %s', exc)

    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={'detail': str(exc)},
    )
