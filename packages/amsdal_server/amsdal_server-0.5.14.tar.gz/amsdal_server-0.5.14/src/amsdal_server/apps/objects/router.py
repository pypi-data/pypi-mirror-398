from fastapi import APIRouter

from amsdal_server.configs.constants import TAG_OBJECTS

router = APIRouter(tags=[TAG_OBJECTS])
