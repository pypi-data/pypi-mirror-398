import logging

from amsdal.contrib.auth.errors import AuthenticationError
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def auth_error_handler(
    request: Request,  # noqa: ARG001
    exc: AuthenticationError,
) -> JSONResponse:
    logger.info('Auth error: %s', exc)

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            'detail': str(exc),
            'code': exc.__class__.__name__,
            'is_mfa_required': exc.__class__.__name__ == 'MFARequiredError',
        },
    )
