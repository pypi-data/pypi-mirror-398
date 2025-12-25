import base64
import logging
import mimetypes
from enum import Enum
from hashlib import md5
from urllib.parse import quote
from urllib.parse import unquote

from amsdal_utils.models.enums import Versions
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import Response

from amsdal_server.apps.common.thumbnail import resize_image
from amsdal_server.apps.objects.router import router
from amsdal_server.apps.objects.services.file_object import ObjectFileApi

logger = logging.getLogger(__name__)


class DispositionType(str, Enum):
    INLINE = 'inline'
    ATTACHMENT = 'attachment'


def _mimetype(filename: str) -> str:
    try:
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    except Exception:
        return 'application/octet-stream'


async def _download_file(
    object_id: str,
    request: Request,
    version_id: str = '',
    width: int | None = None,
    height: int | None = None,
    disposition_type: DispositionType = DispositionType.ATTACHMENT,
) -> Response:
    file_obj = await ObjectFileApi.get_file(
        request.user,
        object_id,
        version_id or Versions.LATEST,
    )

    if not file_obj:
        raise HTTPException(status_code=404, detail='File not found')

    _data = await file_obj.aread_bytes()

    if isinstance(_data, bytes) and _data.startswith((b"b'", b'b"')):
        try:
            # legacy corrupted data
            _data = base64.b64decode(eval(_data))  # noqa: S307
        except SyntaxError:
            pass

    etag = generate_etag(_data, disposition_type.value.encode())

    if request.headers.get('if-none-match') == etag:
        return Response(status_code=304)

    headers = {
        'Cache-Control': 'public, max-age=86400',
        'ETag': etag,
        'Content-Disposition': f'attachment; filename={quote(file_obj.filename)}',
    }
    if disposition_type == DispositionType.INLINE:
        headers['Content-Disposition'] = f'inline; filename={quote(file_obj.filename)}'

    if width and height:
        size = (width, height)
    else:
        size = None

    try:
        content = resize_image(_data, size=size)
    except Exception as e:
        logger.warning('Unable to resize image (probably it is not an image): %s', e, exc_info=True)
        content = _data

    return Response(
        content=content,
        headers=headers,
        media_type=_mimetype(file_obj.filename),
    )


def generate_etag(content: bytes, disposition_type: bytes) -> str:
    return md5(content + disposition_type).hexdigest()  # noqa: S324


@router.get('/api/objects/file-download/{object_id}/')
async def file_download(
    object_id: str,
    request: Request,
    version_id: str = '',
    width: int | None = Query(None),
    height: int | None = Query(None),
    disposition_type: DispositionType = DispositionType.ATTACHMENT,
) -> Response:
    return await _download_file(object_id, request, version_id, width, height, disposition_type=disposition_type)


@router.get('/api/objects/download-file/')
async def download_file(
    request: Request,
    object_id: str,
    version_id: str = '',
    width: int | None = Query(None),
    height: int | None = Query(None),
    disposition_type: DispositionType = DispositionType.ATTACHMENT,
) -> Response:
    return await _download_file(
        unquote(object_id), request, version_id, width, height, disposition_type=disposition_type
    )
