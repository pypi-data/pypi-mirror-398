import json
from hashlib import md5
from typing import Any

from fastapi import BackgroundTasks
from fastapi import Query
from fastapi import Request
from fastapi import Response

from amsdal_server.apps.classes.router import router
from amsdal_server.apps.classes.serializers.class_info import ClassInfo
from amsdal_server.apps.classes.services.classes_api import ClassesApi
from amsdal_server.apps.common.response import AmsdalJSONResponse

CLASS_DETAIL_CACHE = {}


async def _cache_class_details(request: Request, class_name: str) -> tuple[dict[str, Any], str]:
    _data = (await ClassesApi.get_class_by_name(request.user, class_name)).model_dump()

    content_bytes = json.dumps(_data, default=str).encode('utf-8')

    etag = md5(content_bytes).hexdigest()  # noqa: S324
    CLASS_DETAIL_CACHE[etag] = _data

    return _data, etag


@router.get('/api/classes/{class_name}/', response_model=ClassInfo)
async def get_class(
    request: Request,
    class_name: str,
    background_tasks: BackgroundTasks,
    cache_control: int | None = Query(
        default=None,
        description='Cache-Control max-age value',
    ),
) -> Response:
    etag = request.headers.get('if-none-match')

    if etag in CLASS_DETAIL_CACHE:
        CLASS_DETAIL_CACHE.pop(etag)
        background_tasks.add_task(
            _cache_class_details,
            request,
            class_name,
        )
        return Response(status_code=304)

    headers = {}
    if cache_control:
        headers['Cache-Control'] = f'public, max-age={cache_control}'

    result, etag = await _cache_class_details(request, class_name)
    headers['ETag'] = etag

    return AmsdalJSONResponse(
        content=result,
        headers=headers,
    )
