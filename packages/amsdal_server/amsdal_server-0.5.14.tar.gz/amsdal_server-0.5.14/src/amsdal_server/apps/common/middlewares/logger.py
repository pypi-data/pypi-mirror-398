import logging
import time

from amsdal.context.manager import AmsdalContextManager
from amsdal.contrib.auth.errors import AuthenticationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from amsdal_server.apps.common.error_handlers.invalid_auth import auth_error_handler

logger = logging.getLogger('amsdal_server.http')


class LoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        before_time = time.perf_counter()
        error: BaseException | None = None
        status_code: int = -1

        AmsdalContextManager().add_to_context('request', request)

        try:
            response = await call_next(request)

        except AuthenticationError as exc:
            response = await auth_error_handler(request, exc)
            status_code = response.status_code
            error = exc
        except BaseException as exc:
            status_code = HTTP_500_INTERNAL_SERVER_ERROR
            error = exc
            raise
        else:
            status_code = response.status_code
        finally:
            after_time = time.perf_counter()

            try:
                user = request.user
            except AssertionError:
                user = None

            path = self.get_path_template(request)

            log = logger.error if error else logger.info
            log(
                'method=%s path=%s status=%s time=%.3f user=%s host=%s',
                request.method,
                path,
                status_code,
                after_time - before_time,
                user,
                request.client.host if request.client else None,
            )
        return response

    @staticmethod
    def get_path_template(request: Request) -> str:
        for route in request.app.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return route.path
        return request.url.path
