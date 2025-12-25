import json
from hashlib import md5
from typing import Any

from fastapi import BackgroundTasks
from fastapi import Query
from fastapi import Request
from fastapi import Response

from amsdal_server.apps.common.response import AmsdalJSONResponse
from amsdal_server.apps.common.serializers.objects_response import ObjectsResponse
from amsdal_server.apps.common.serializers.objects_response import ObjectsResponseControl
from amsdal_server.apps.transactions.router import router
from amsdal_server.apps.transactions.services.transaction_api import TransactionApi

TRANSACTIONS_CACHE = {}


async def _cache_transaction_list() -> tuple[dict[str, Any], str]:
    _data = TransactionApi.get_transactions().model_dump()

    content_bytes = json.dumps(_data, default=str).encode('utf-8')

    etag = md5(content_bytes).hexdigest()  # noqa: S324
    TRANSACTIONS_CACHE[etag] = _data

    return _data, etag


async def _cache_transaction_detail(transaction_name: str) -> tuple[dict[str, Any], str]:
    _data = TransactionApi.get_transaction(transaction_name).model_dump()

    content_bytes = json.dumps(_data, default=str).encode('utf-8')

    etag = md5(content_bytes).hexdigest()  # noqa: S324
    TRANSACTIONS_CACHE[etag] = _data

    return _data, etag


@router.get('/api/transactions/', response_model=ObjectsResponse)
async def transaction_list(
    request: Request,
    background_tasks: BackgroundTasks,
    cache_control: int | None = Query(
        default=None,
        description='Cache-Control max-age value',
    ),
) -> Response:
    etag = request.headers.get('if-none-match')

    if etag in TRANSACTIONS_CACHE:
        TRANSACTIONS_CACHE.pop(etag)
        background_tasks.add_task(_cache_transaction_list)
        return Response(status_code=304)

    headers = {}
    if cache_control:
        headers['Cache-Control'] = f'public, max-age={cache_control}'

    result, etag = await _cache_transaction_list()
    headers['ETag'] = etag

    return AmsdalJSONResponse(
        content=result,
        headers=headers,
    )


@router.get('/api/transactions/{transaction_name}/', response_model=ObjectsResponseControl)
async def transaction_detail(
    request: Request,
    background_tasks: BackgroundTasks,
    transaction_name: str,
    cache_control: int | None = Query(
        default=None,
        description='Cache-Control max-age value',
    ),
) -> Response:
    etag = request.headers.get('if-none-match')

    if etag in TRANSACTIONS_CACHE:
        TRANSACTIONS_CACHE.pop(etag)
        background_tasks.add_task(_cache_transaction_detail, transaction_name)
        return Response(status_code=304)

    headers = {}
    if cache_control:
        headers['Cache-Control'] = f'public, max-age={cache_control}'

    result, etag = await _cache_transaction_detail(transaction_name)
    headers['ETag'] = etag

    return AmsdalJSONResponse(
        content=result,
        headers=headers,
    )
