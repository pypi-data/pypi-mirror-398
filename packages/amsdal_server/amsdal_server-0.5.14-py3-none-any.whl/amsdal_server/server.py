import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from amsdal.contrib.auth.errors import AuthenticationError
from amsdal_models.errors import AmsdalValidationError
from amsdal_utils.config.manager import AmsdalConfigManager
from amsdal_utils.lifecycle.enum import LifecycleEvent
from amsdal_utils.lifecycle.producer import LifecycleProducer
from fastapi import Depends
from fastapi import FastAPI
from fastapi import responses
from fastapi.security.api_key import APIKeyHeader
from pydantic import ValidationError

from amsdal_server.apps.classes.errors import ClassNotFoundError
from amsdal_server.apps.classes.errors import TransactionNotFoundError
from amsdal_server.apps.common.error_handlers.class_not_found import class_not_found_handler
from amsdal_server.apps.common.error_handlers.invalid_auth import auth_error_handler
from amsdal_server.apps.common.error_handlers.permission_error import permission_error_handler
from amsdal_server.apps.common.error_handlers.validation_error_handler import validation_error_handler
from amsdal_server.apps.common.error_handlers.validation_error_handler import value_error_handler
from amsdal_server.apps.common.errors import AmsdalPermissionError
from amsdal_server.apps.common.errors import AmsdalTransactionError
from amsdal_server.apps.common.middlewares.utils import init_middlewares
from amsdal_server.apps.common.otel import setting_otlp
from amsdal_server.apps.common.utils import async_build_missing_models
from amsdal_server.apps.common.utils import build_missing_models
from amsdal_server.apps.router import init_routers
from amsdal_server.configs.constants import APP_DESCRIPTION
from amsdal_server.configs.main import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    from amsdal_server.apps.common.thumbnail import memory

    if AmsdalConfigManager().get_config().async_mode:
        await LifecycleProducer.publish_async(LifecycleEvent.ON_SERVER_STARTUP)
    else:
        LifecycleProducer.publish(LifecycleEvent.ON_SERVER_STARTUP)

    memory.reduce_size(
        bytes_limit=settings.THUMBNAIL_CACHE_BITES_LIMIT,
        age_limit=settings.THUMBNAIL_CACHE_AGE_LIMIT,
    )

    if AmsdalConfigManager().get_config().async_mode:
        missed_models = await async_build_missing_models()
    else:
        missed_models = build_missing_models()

    if missed_models:
        logger.warning(f'Missed models: {", ".join(missed_models)}')

    yield


app = FastAPI(
    debug=settings.DEBUG,
    title=settings.APP_NAME,
    description=APP_DESCRIPTION,
    docs_url='/docs' if settings.IS_DOCS_ENABLED else None,
    default_response_class=responses.ORJSONResponse,
    lifespan=lifespan,
    dependencies=[
        Depends(
            APIKeyHeader(
                name=settings.AUTHORIZATION_HEADER,
                auto_error=False,
                scheme_name='AmsdalAuth',
            )
        )
    ],
)
init_routers(app)
init_middlewares(app)

if settings.OTLP_ENDPOINT:
    setting_otlp(app, settings.APP_NAME, settings.OTLP_ENDPOINT)

app.exception_handler(ValidationError)(validation_error_handler)
app.exception_handler(ValueError)(value_error_handler)
app.exception_handler(AmsdalTransactionError)(value_error_handler)
app.exception_handler(AmsdalValidationError)(value_error_handler)
app.exception_handler(ClassNotFoundError)(class_not_found_handler)
app.exception_handler(TransactionNotFoundError)(class_not_found_handler)
app.exception_handler(AuthenticationError)(auth_error_handler)
app.exception_handler(AmsdalPermissionError)(permission_error_handler)


def start(
    *,
    is_development_mode: bool = False,
    port: int | None = None,
    host: str | None = None,
    **kwargs: Any,
) -> None:
    _app = '__main__:app' if is_development_mode else app
    """Start the server."""
    uvicorn.run(
        _app,
        host=host or settings.HOST,
        port=port or settings.PORT,
        # We already log in LoggerMiddleware
        # no need to duplicate these logs with uvicorn
        access_log=False,
        reload=is_development_mode,
        **kwargs,
    )


if __name__ == '__main__':
    start(is_development_mode=True)
