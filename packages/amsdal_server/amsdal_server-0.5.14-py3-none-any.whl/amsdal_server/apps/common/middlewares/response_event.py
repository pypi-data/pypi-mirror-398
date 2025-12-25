import json
import logging
from collections.abc import AsyncGenerator

from amsdal.contrib.frontend_configs.constants import ON_RESPONSE_EVENT
from amsdal_utils.config.manager import AmsdalConfigManager
from amsdal_utils.lifecycle.producer import LifecycleProducer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.responses import StreamingResponse

logger = logging.getLogger('amsdal_server.http')
CHUNK_SIZE = 512


async def _iterate_data(data: bytes) -> AsyncGenerator[bytes, bytes]:
    for i in range(0, len(data), CHUNK_SIZE):
        chunk = data[i : i + CHUNK_SIZE]

        yield chunk


class ResponseEventMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response: StreamingResponse = await call_next(request)  # type: ignore[assignment]

        if 'Content-Type' not in response.headers or response.headers['Content-Type'] != 'application/json':
            return response

        try:
            data = b''
            async for chunk in response.body_iterator:
                data += chunk  # type: ignore[operator]

            if data:
                response_dict = json.loads(data)

                if AmsdalConfigManager().get_config().async_mode:
                    await LifecycleProducer.publish_async(
                        ON_RESPONSE_EVENT,  # type: ignore[arg-type]
                        request=request,
                        response=response_dict,
                    )
                else:
                    LifecycleProducer.publish(
                        ON_RESPONSE_EVENT,  # type: ignore[arg-type]
                        request=request,
                        response=response_dict,
                    )

                _result = JSONResponse.render(
                    response,  # type: ignore[arg-type]
                    response_dict,
                )
                response.headers['Content-Length'] = str(len(_result))
                response.body_iterator = _iterate_data(_result)
            else:
                response.body_iterator = _iterate_data(data)
        except Exception as exc:
            response.body_iterator = _iterate_data(data)
            logger.exception(exc)

        return response
