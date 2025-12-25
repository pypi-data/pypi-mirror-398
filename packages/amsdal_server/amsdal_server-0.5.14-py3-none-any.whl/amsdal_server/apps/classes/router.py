from fastapi import APIRouter

from amsdal_server.configs.constants import TAG_CLASSES

router = APIRouter(tags=[TAG_CLASSES])
