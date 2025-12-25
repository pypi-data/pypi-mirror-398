import json
import urllib.parse
from hashlib import md5
from typing import Any

from fastapi import BackgroundTasks
from fastapi import Query
from fastapi import Request
from fastapi import Response

from amsdal_server.apps.common.response import AmsdalJSONResponse
from amsdal_server.apps.common.serializers.objects_response import ObjectsResponse
from amsdal_server.apps.objects.router import router
from amsdal_server.apps.objects.services.object_versions_api import ObjectVersionsApi
from amsdal_server.apps.objects.utils import normalize_address

OBJECT_DETAIL_CACHE = {}


async def _cache_object_detail(
    request: Request,
    address: str,
    version_id: str,
    all_versions: bool,  # noqa: FBT001
    include_metadata: bool,  # noqa: FBT001
    file_optimized: bool,  # noqa: FBT001
    select_related: str | None,
) -> tuple[dict[str, Any], str]:
    _select_related = select_related.split(',') if select_related else None

    _data = (
        await ObjectVersionsApi.get_object_versions(
            request.user,
            base_url=str(request.base_url),
            address=address,
            version_id=version_id,
            all_versions=all_versions,
            include_metadata=include_metadata,
            file_optimized=file_optimized,
            select_related=_select_related,
        )
    ).model_dump()

    content_bytes = json.dumps(_data, default=str).encode('utf-8')

    etag = md5(content_bytes).hexdigest()  # noqa: S324
    OBJECT_DETAIL_CACHE[etag] = _data

    return _data, etag


@router.get('/api/objects/{address:path}/', response_model=ObjectsResponse)
async def object_detail(
    address: str,
    request: Request,
    background_tasks: BackgroundTasks,
    version_id: str = '',
    *,
    all_versions: bool = False,
    include_metadata: bool = True,
    file_optimized: bool = False,
    select_related: str | None = Query(
        default=None,
        description='Comma-separated list of related fields to fetch',
        examples=['field1', 'field1,field2'],
    ),
    cache_control: int | None = Query(
        default=None,
        description='Cache-Control max-age value',
    ),
) -> Response:
    etag = request.headers.get('if-none-match')
    normalized_address = normalize_address(urllib.parse.unquote(address))

    if etag in OBJECT_DETAIL_CACHE:
        OBJECT_DETAIL_CACHE.pop(etag)
        background_tasks.add_task(
            _cache_object_detail,
            request,
            normalized_address,
            version_id,
            all_versions,
            include_metadata,
            file_optimized,
            select_related,
        )
        return Response(status_code=304)

    headers = {}
    if cache_control:
        headers['Cache-Control'] = f'public, max-age={cache_control}'

    result, etag = await _cache_object_detail(
        request,
        normalized_address,
        version_id=version_id,
        all_versions=all_versions,
        include_metadata=include_metadata,
        file_optimized=file_optimized,
        select_related=select_related,
    )
    headers['ETag'] = etag

    return AmsdalJSONResponse(
        content=result,
        headers=headers,
    )
