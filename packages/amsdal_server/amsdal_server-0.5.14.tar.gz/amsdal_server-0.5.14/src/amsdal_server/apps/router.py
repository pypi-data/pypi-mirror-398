import importlib
import pkgutil
from importlib import import_module
from types import ModuleType

from fastapi import APIRouter
from fastapi import FastAPI

router = APIRouter()


def init_routers(app: FastAPI) -> None:
    from amsdal_server.configs.main import settings

    app_module: ModuleType

    for app_module in settings.INSTALLED_APPS:  # type: ignore[assignment]
        router_path = f'{app_module.__package__}.router'

        try:
            app_router = import_module(router_path)
        except ImportError:
            continue

        if hasattr(app_router, 'router'):
            load_controllers(app_module.__package__)
            app.include_router(app_router.router)


def load_controllers(package: str | None) -> None:
    try:
        views: ModuleType = import_module(f'{package}.controllers')
    except ImportError:
        return

    if views.__package__ and views.__package__ != package:
        import_submodules(views.__package__)


def import_submodules(package_str: str, *, recursive: bool = True) -> None:
    package: ModuleType = importlib.import_module(package_str)

    for _loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name

        importlib.import_module(full_name)

        if recursive and is_pkg:
            import_submodules(full_name)
