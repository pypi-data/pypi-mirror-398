from importlib import import_module
from typing import Any

from fastapi import FastAPI
from starlette.requests import Request
from starlette.types import Message


def init_middlewares(app: FastAPI) -> None:
    from amsdal_server.configs.main import settings

    for app_module in settings.MIDDLEWARES:
        params: dict[str, Any] = {}

        if isinstance(app_module, tuple):
            app_module, _params = app_module  # noqa: PLW2901

            for key, value in _params.items():
                if isinstance(value, str) and value.startswith('amsdal') and '.' in value:
                    module_path, class_name = value.rsplit('.', 1)
                    param_module = import_module(module_path)
                    params[key] = getattr(param_module, class_name)()
                else:
                    params[key] = value

        middleware_path, middleware_class = app_module.rsplit('.', 1)

        middleware_module = import_module(middleware_path)

        app.add_middleware(
            getattr(middleware_module, middleware_class),
            **params,
        )


async def set_req_body(request: Request, body: bytes) -> None:
    async def receive() -> Message:
        return {'type': 'http.request', 'body': body}

    request._receive = receive
