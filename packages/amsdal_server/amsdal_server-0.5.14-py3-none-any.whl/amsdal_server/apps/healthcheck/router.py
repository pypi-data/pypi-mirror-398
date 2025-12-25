from fastapi import APIRouter

from amsdal_server.configs.constants import TAG_PROBES

router = APIRouter(tags=[TAG_PROBES])
