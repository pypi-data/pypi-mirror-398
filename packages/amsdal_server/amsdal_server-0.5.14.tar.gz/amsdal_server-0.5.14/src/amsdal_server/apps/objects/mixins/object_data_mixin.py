import base64
import inspect
import urllib.parse
from typing import Any

from amsdal_models.classes.model import LegacyModel
from amsdal_models.classes.model import Model
from amsdal_models.classes.utils import build_class_meta_schema_reference
from amsdal_models.classes.utils import build_class_schema_reference
from amsdal_models.classes.utils import get_custom_properties
from amsdal_utils.models.data_models.metadata import Metadata
from amsdal_utils.models.enums import Versions

from amsdal_server.apps.common.serializers.fields_restriction import FieldsRestriction


class ObjectDataMixin:
    @classmethod
    async def build_object_data(
        cls,
        item: Model,
        base_url: str,
        *,
        include_metadata: bool = False,
        fields_restrictions: dict[str, FieldsRestriction] | None = None,
        load_references: bool = False,
        is_file_object: bool = False,
        is_from_lakehouse: bool = False,
    ) -> dict[str, Any]:
        if load_references:
            _item_data = await item.amodel_dump()
        else:
            _item_data = await item.amodel_dump_refs()

        _item_data = cls._encode_bytes(_item_data)

        for name in get_custom_properties(item.__class__):
            _item_data[name] = getattr(item, name)

            if inspect.isawaitable(_item_data[name]):
                _item_data[name] = await _item_data[name]

        if include_metadata:
            _metadata = cls.get_metadata(item, is_from_lakehouse=is_from_lakehouse)
            _item_data['_metadata'] = _metadata.model_dump()

            metadata_restrictions = fields_restrictions.get('Metadata', None) if fields_restrictions else None
            if metadata_restrictions and metadata_restrictions.fields:
                new_metadata = {k: v for k, v in _item_data['_metadata'].items() if k in metadata_restrictions.fields}
                # we really want to filter ot fields if thy are valid
                if new_metadata:
                    _item_data['_metadata'] = new_metadata

            _item_data['_metadata']['next_version'] = _metadata.next_version
            _item_data['_metadata']['address'] = _metadata.address.model_dump()
            _item_data['_metadata']['lakehouse_address'] = urllib.parse.quote(_metadata.address.to_string())
        else:
            _item_data.pop('_metadata', None)

        if is_file_object:
            _metadata = cls.get_metadata(item, is_from_lakehouse=is_from_lakehouse)
            _object_id = _metadata.address.object_id
            _object_version = _metadata.address.object_version
            _item_data['data'] = (
                f'{base_url}api/objects/download-file/'
                f'?version_id={urllib.parse.quote(_object_version)}'
                f'&object_id={urllib.parse.quote(_object_id)}'  # type: ignore[arg-type]
            )

        return _item_data

    @classmethod
    def get_metadata(
        cls,
        item: Model,
        *,
        is_from_lakehouse: bool = False,
    ) -> Metadata:
        if is_from_lakehouse:
            return item.get_metadata()

        _class_name = item.__class__.__name__
        _origin_class = item.__class__

        if isinstance(item, LegacyModel):
            _class_name = item.original_class.__name__
            _origin_class = item.original_class
        elif _class_name.endswith('Partial'):
            _class_name = _class_name[:-7]

        return Metadata(
            object_id=item.object_id,
            object_version=Versions.LATEST,
            class_schema_reference=build_class_schema_reference(_class_name, _origin_class),
            class_meta_schema_reference=build_class_meta_schema_reference(
                _class_name,
                item.object_id,
            ),
        )

    @classmethod
    def _encode_bytes(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {key: cls._encode_bytes(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [cls._encode_bytes(item) for item in data]
        elif isinstance(data, bytes | bytearray):
            return f'data:binary;base64, {base64.b64encode(data).decode("utf-8")}'
        return data
