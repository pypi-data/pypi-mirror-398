from fastapi import APIRouter

from amsdal_server.configs.constants import TAG_TRANSACTIONS

router = APIRouter(tags=[TAG_TRANSACTIONS])
