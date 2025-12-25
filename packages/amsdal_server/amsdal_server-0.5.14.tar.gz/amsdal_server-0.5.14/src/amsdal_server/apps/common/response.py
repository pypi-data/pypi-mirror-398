import json
from datetime import datetime
from json import JSONEncoder
from json.encoder import _make_iterencode  # type: ignore[attr-defined]
from json.encoder import encode_basestring
from json.encoder import encode_basestring_ascii
from typing import Any

from starlette.responses import JSONResponse

try:
    from _json import make_encoder as c_make_encoder
except ImportError:
    c_make_encoder = None  # type: ignore[misc, assignment]

INFINITY = float('inf')


class CustomJSONEncoder(JSONEncoder):
    def iterencode(self, o: Any, _one_shot: bool = False) -> Any:  # noqa: FBT001, FBT002
        """Encode the given object and yield each string
        representation as available.

        For example::

            for chunk in JSONEncoder().iterencode(bigobject):
                mysocket.write(chunk)

        """

        markers: dict[Any, Any] | None = {} if self.check_circular else None

        if self.ensure_ascii:
            _encoder = encode_basestring_ascii
        else:
            _encoder = encode_basestring

        def floatstr(  # type: ignore[no-untyped-def]
            o,
            allow_nan=self.allow_nan,
            _repr=float.__repr__,
            _inf=INFINITY,
            _neginf=-INFINITY,
        ):
            # Check for specials.  Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on the
            # internals.

            if o != o:  # noqa: PLR0124
                text = 'NaN'
            elif o == _inf:
                # TODO: our custom implementation
                return '"Infinity"'
            elif o == _neginf:
                # TODO: our custom implementation
                return '"-Infinity"'
            else:
                return _repr(o)

            if not allow_nan:
                raise ValueError('Out of range float values are not JSON compliant: ' + repr(o))

            return text

        # TODO: due to the way we handle Infinity, we cannot use c_make_iterencode
        _iterencode = _make_iterencode(
            markers,
            self.default,
            _encoder,
            self.indent,
            floatstr,
            self.key_separator,
            self.item_separator,
            self.sort_keys,
            self.skipkeys,
            _one_shot,
        )
        return _iterencode(o, 0)


def default_json_encoder(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


class AmsdalJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(',', ':'),
            default=default_json_encoder,
            cls=CustomJSONEncoder,
        ).encode('utf-8')
