import json
from hashlib import md5
from typing import Any

from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import Query
from fastapi import Request
from fastapi import Response

from amsdal_server.apps.common.depends import get_fields_restrictions
from amsdal_server.apps.common.depends import get_filters
from amsdal_server.apps.common.response import AmsdalJSONResponse
from amsdal_server.apps.common.serializers.fields_restriction import FieldsRestriction
from amsdal_server.apps.common.serializers.filter import Filter
from amsdal_server.apps.common.serializers.objects_response import ObjectsResponse
from amsdal_server.apps.objects.router import router
from amsdal_server.apps.objects.services.object_list_api import ObjectListApi

OBJECT_LIST_CACHE = {}


async def _cache_object_list(
    request: Request,
    class_name: str,
    *,
    include_metadata: bool,
    include_subclasses: bool,
    load_references: bool,
    all_versions: bool,
    file_optimized: bool,
    fields_restrictions: dict[str, FieldsRestriction],
    filters: list[Filter],
    page: int,
    page_size: int | None,
    ordering: list[str] | None,
    select_related: str | None,
) -> tuple[dict[str, Any], str]:
    _select_related = select_related.split(',') if select_related else None

    _data = (
        await ObjectListApi.fetch_objects(
            request.user,
            base_url=str(request.base_url),
            class_name=class_name,
            filters=filters,
            fields_restrictions=fields_restrictions,
            include_metadata=include_metadata,
            include_subclasses=include_subclasses,
            load_references=load_references,
            all_versions=all_versions,
            file_optimized=file_optimized,
            page=page,
            page_size=page_size,
            ordering=ordering,
            select_related=_select_related,
        )
    ).model_dump()

    content_bytes = json.dumps(_data, default=str).encode('utf-8')

    etag = md5(content_bytes).hexdigest()  # noqa: S324
    OBJECT_LIST_CACHE[etag] = _data

    return _data, etag


@router.get('/api/objects/', response_model_exclude_none=True, response_model=ObjectsResponse)
async def object_list(
    request: Request,
    class_name: str,
    background_tasks: BackgroundTasks,
    *,
    include_metadata: bool = True,
    include_subclasses: bool = False,
    load_references: bool = False,
    all_versions: bool = False,
    file_optimized: bool = False,
    fields_restrictions: dict[str, FieldsRestriction] = Depends(get_fields_restrictions),
    filters: list[Filter] = Depends(get_filters),
    page: int = 1,
    page_size: int | None = Query(default=None),
    ordering: list[str] | None = Query(default=None),
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

    if etag in OBJECT_LIST_CACHE:
        OBJECT_LIST_CACHE.pop(etag)
        background_tasks.add_task(
            _cache_object_list,
            request,
            class_name,
            include_metadata=include_metadata,
            include_subclasses=include_subclasses,
            load_references=load_references,
            all_versions=all_versions,
            file_optimized=file_optimized,
            fields_restrictions=fields_restrictions,
            filters=filters,
            page=page,
            page_size=page_size,
            ordering=ordering,
            select_related=select_related,
        )
        return Response(status_code=304)

    headers = {}
    if cache_control:
        headers['Cache-Control'] = f'public, max-age={cache_control}'

    result, etag = await _cache_object_list(
        request,
        class_name,
        include_metadata=include_metadata,
        include_subclasses=include_subclasses,
        load_references=load_references,
        all_versions=all_versions,
        file_optimized=file_optimized,
        fields_restrictions=fields_restrictions,
        filters=filters,
        page=page,
        page_size=page_size,
        ordering=ordering,
        select_related=select_related,
    )
    headers['ETag'] = etag

    return AmsdalJSONResponse(
        content=result,
        headers=headers,
    )
