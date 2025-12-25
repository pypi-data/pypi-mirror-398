import logging

from fastapi import Request
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def validation_error_handler(
    request: Request,  # noqa: ARG001
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={'detail': jsonable_encoder(exc.errors())},
    )


async def value_error_handler(
    request: Request,  # noqa: ARG001
    exc: ValueError,
) -> JSONResponse:
    logger.exception('Value error: %s', exc, exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={'detail': str(exc)},
    )
