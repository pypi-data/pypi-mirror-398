import json
from hashlib import md5
from typing import Any

from fastapi import BackgroundTasks
from fastapi import Query
from fastapi import Request
from fastapi import Response

from amsdal_server.apps.classes.router import router
from amsdal_server.apps.classes.services.classes_api import ClassesApi
from amsdal_server.apps.common.response import AmsdalJSONResponse
from amsdal_server.apps.common.serializers.column_format import ColumnFormat
from amsdal_server.apps.common.serializers.column_response import ColumnInfo
from amsdal_server.apps.common.serializers.objects_response import ObjectsResponse

CLASS_LIST_CACHE = {}


async def _cache_class_list(request: Request) -> tuple[dict[str, Any], str]:
    class_items = await ClassesApi.get_classes(request.user)
    _data = ObjectsResponse(
        columns=[
            ColumnInfo(
                key='class',
                label='Class',
                column_format=ColumnFormat(cellTemplate='ClassLinkTemplate'),
            ),
            ColumnInfo(key='count', label='Count'),
            ColumnInfo(key='properties', label='Properties'),
        ],
        total=len(class_items),
        rows=class_items,
    ).model_dump()

    content_bytes = json.dumps(_data, default=str).encode('utf-8')

    etag = md5(content_bytes).hexdigest()  # noqa: S324
    CLASS_LIST_CACHE[etag] = _data

    return _data, etag


@router.get('/api/classes/', response_model_exclude_none=True, response_model=ObjectsResponse)
async def class_list(
    request: Request,
    background_tasks: BackgroundTasks,
    cache_control: int | None = Query(
        default=None,
        description='Cache-Control max-age value',
    ),
) -> Response:
    etag = request.headers.get('if-none-match')

    if etag in CLASS_LIST_CACHE:
        CLASS_LIST_CACHE.pop(etag)
        background_tasks.add_task(
            _cache_class_list,
            request,
        )
        return Response(status_code=304)

    headers = {}
    if cache_control:
        headers['Cache-Control'] = f'public, max-age={cache_control}'

    result, etag = await _cache_class_list(request)
    headers['ETag'] = etag

    return AmsdalJSONResponse(
        content=result,
        headers=headers,
    )
