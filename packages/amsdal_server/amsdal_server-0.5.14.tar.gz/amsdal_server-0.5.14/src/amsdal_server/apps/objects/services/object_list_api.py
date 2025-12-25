from typing import Any

from amsdal_models.classes.constants import FILE_CLASS_NAME
from amsdal_models.classes.model import Model
from amsdal_models.classes.relationships.constants import FOREIGN_KEYS
from amsdal_models.querysets.executor import LAKEHOUSE_DB_ALIAS
from amsdal_utils.config.manager import AmsdalConfigManager
from amsdal_utils.models.base import ModelBase
from amsdal_utils.models.enums import Versions
from amsdal_utils.query.utils import Q
from starlette.authentication import BaseUser

from amsdal_server.apps.classes.mixins.column_info_mixin import ColumnInfoMixin
from amsdal_server.apps.classes.mixins.model_class_info import ModelClassMixin
from amsdal_server.apps.common.mixins.permissions_mixin import PermissionsMixin
from amsdal_server.apps.common.serializers.column_response import ColumnInfo
from amsdal_server.apps.common.serializers.fields_restriction import FieldsRestriction
from amsdal_server.apps.common.serializers.filter import Filter
from amsdal_server.apps.common.serializers.objects_response import ObjectsResponse
from amsdal_server.apps.common.utils import get_subclasses
from amsdal_server.apps.objects.mixins.object_data_mixin import ObjectDataMixin


class ObjectListApi(PermissionsMixin, ModelClassMixin, ColumnInfoMixin, ObjectDataMixin):
    @classmethod
    def _resolve_reference_filters(
        cls,
        model_class: type[Model],
        filters: list[Filter],
    ) -> list[Filter]:
        """Convert partition key strings to actual object references for reference fields."""
        fk_fields = getattr(model_class, FOREIGN_KEYS, [])
        if not fk_fields:
            return filters

        resolved_filters = []
        for filter_obj in filters:
            # Check if this is a direct reference field filter (no __ in key)
            filter_key = filter_obj.key
            if '__' not in filter_key and filter_key in fk_fields:
                # This is a direct reference filter, need to resolve the partition key to an object
                field_info = model_class.model_fields[filter_key]
                ref_model_class = field_info.annotation

                # Handle Optional[] and Union[] types
                if (
                    ref_model_class is not None
                    and hasattr(ref_model_class, '__origin__')
                    and hasattr(ref_model_class, '__args__')
                ):
                    # For Optional/Union, get the first non-None type argument
                    args = ref_model_class.__args__
                    for arg in args:
                        if arg is not type(None) and hasattr(arg, 'objects'):
                            ref_model_class = arg
                            break

                # Ensure ref_model_class is valid and has objects attribute
                if ref_model_class is None or not hasattr(ref_model_class, 'objects'):
                    resolved_filters.append(filter_obj)
                    continue

                try:
                    # Fetch the referenced object by partition key
                    ref_obj = ref_model_class.objects.get(_address__object_id=filter_obj.target).execute()
                    # Create a new filter with the object instead of partition key
                    resolved_filters.append(
                        Filter(
                            key=filter_obj.key,
                            target=ref_obj,
                            filter_type=filter_obj.filter_type,
                        )
                    )
                except Exception:
                    # If we can't fetch the object, keep the original filter (will fail later with clear error)
                    resolved_filters.append(filter_obj)
            else:
                # Not a direct reference filter, keep as-is
                resolved_filters.append(filter_obj)

        return resolved_filters

    @classmethod
    async def fetch_objects(
        cls,
        user: BaseUser,
        base_url: str,
        class_name: str,
        *,
        filters: list[Filter] | None = None,
        include_metadata: bool = False,
        include_subclasses: bool = False,
        fields_restrictions: dict[str, FieldsRestriction] | None = None,
        load_references: bool = False,
        all_versions: bool = False,
        file_optimized: bool = False,
        page: int = 1,
        page_size: int | None = None,
        ordering: list[str] | None = None,
        select_related: list[str] | None = None,
    ) -> ObjectsResponse:
        if AmsdalConfigManager().get_config().async_mode:
            return await cls.fetch_objects_async(
                user,
                base_url,
                class_name,
                filters=filters,
                include_metadata=include_metadata,
                include_subclasses=include_subclasses,
                fields_restrictions=fields_restrictions,
                load_references=load_references,
                all_versions=all_versions,
                file_optimized=file_optimized,
                page=page,
                page_size=page_size,
                ordering=ordering,
                select_related=select_related,
            )

        return await cls.fetch_objects_sync(
            user,
            base_url,
            class_name,
            filters=filters,
            include_metadata=include_metadata,
            include_subclasses=include_subclasses,
            fields_restrictions=fields_restrictions,
            load_references=load_references,
            all_versions=all_versions,
            file_optimized=file_optimized,
            page=page,
            page_size=page_size,
            ordering=ordering,
            select_related=select_related,
        )

    @classmethod
    async def fetch_objects_async(
        cls,
        user: BaseUser,
        base_url: str,
        class_name: str,
        *,
        filters: list[Filter] | None = None,
        include_metadata: bool = False,
        include_subclasses: bool = False,
        fields_restrictions: dict[str, FieldsRestriction] | None = None,
        load_references: bool = False,
        all_versions: bool = False,
        file_optimized: bool = False,
        page: int = 1,
        page_size: int | None = None,
        ordering: list[str] | None = None,
        select_related: list[str] | None = None,
    ) -> ObjectsResponse:
        model_class = await cls.async_get_model_class_by_name(class_name)
        permissions_info = await cls.async_get_permissions_info(model_class, user)
        class_item: Model = await cls.get_class_objects_qs().get(_address__object_id=class_name).aexecute()

        class_properties: list[ColumnInfo] = await cls.aget_class_properties_by_class_and_meta(
            class_item,
        )
        available_columns = [column.key for column in class_properties]
        available_columns += ['_metadata']
        fields_restriction = fields_restrictions.get(class_name) if fields_restrictions else None

        if fields_restriction:
            class_properties = [column for column in class_properties if column.key in fields_restriction.fields]
            fields_restriction.fields = [field for field in fields_restriction.fields if field in available_columns]

        if not permissions_info.has_read_permission:
            return ObjectsResponse(
                columns=class_properties,
                rows=[],
                total=0,
            )

        _filters = [
            _filter
            for _filter in (filters or [])
            if any(
                _filter.key == available_column or _filter.key.startswith(f'{available_column}__')
                for available_column in available_columns
            )
        ]

        rows, total = await cls._async_fetch_objects(
            base_url,
            model_class,
            filters=_filters,
            fields_restrictions=fields_restrictions,
            include_metadata=include_metadata,
            include_subclasses=include_subclasses,
            load_references=load_references,
            all_versions=all_versions,
            file_optimized=file_optimized,
            page=page,
            page_size=page_size,
            ordering=ordering,
            select_related=select_related,
        )

        return ObjectsResponse(
            columns=class_properties,
            rows=rows,
            total=total,
        )

    @classmethod
    async def fetch_objects_sync(
        cls,
        user: BaseUser,
        base_url: str,
        class_name: str,
        *,
        filters: list[Filter] | None = None,
        include_metadata: bool = False,
        include_subclasses: bool = False,
        fields_restrictions: dict[str, FieldsRestriction] | None = None,
        load_references: bool = False,
        all_versions: bool = False,
        file_optimized: bool = False,
        page: int = 1,
        page_size: int | None = None,
        ordering: list[str] | None = None,
        select_related: list[str] | None = None,
    ) -> ObjectsResponse:
        model_class = cls.get_model_class_by_name(class_name)
        permissions_info = cls.get_permissions_info(model_class, user)
        class_item: Model = cls.get_class_objects_qs().get(_address__object_id=class_name).execute()

        class_properties: list[ColumnInfo] = cls.get_class_properties_by_class_object(
            class_item,
        )
        available_columns = [column.key for column in class_properties]
        available_columns += ['_metadata']
        fields_restriction = fields_restrictions.get(class_name) if fields_restrictions else None

        if fields_restriction:
            class_properties = [column for column in class_properties if column.key in fields_restriction.fields]
            fields_restriction.fields = [field for field in fields_restriction.fields if field in available_columns]

        if not permissions_info.has_read_permission:
            return ObjectsResponse(
                columns=class_properties,
                rows=[],
                total=0,
            )

        _filters = [
            _filter
            for _filter in (filters or [])
            if any(
                _filter.key == available_column or _filter.key.startswith(f'{available_column}__')
                for available_column in available_columns
            )
        ]

        rows, total = await cls._fetch_objects(
            base_url,
            model_class,
            filters=_filters,
            fields_restrictions=fields_restrictions,
            include_metadata=include_metadata,
            include_subclasses=include_subclasses,
            load_references=load_references,
            all_versions=all_versions,
            file_optimized=file_optimized,
            page=page,
            page_size=page_size,
            ordering=ordering,
            select_related=select_related,
        )

        return ObjectsResponse(
            columns=class_properties,
            rows=rows,
            total=total,
        )

    @classmethod
    async def _fetch_objects(
        cls,
        base_url: str,
        model_class: type[Model],
        filters: list[Filter],
        *,
        include_subclasses: bool = False,
        include_metadata: bool = False,
        fields_restrictions: dict[str, FieldsRestriction] | None = None,
        load_references: bool = False,
        all_versions: bool = False,
        file_optimized: bool = False,
        page: int = 1,
        page_size: int | None = None,
        ordering: list[str] | None = None,
        select_related: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        result: list[dict[str, Any]] = []
        total: int = 0
        classes: list[type[ModelBase]] = [model_class]

        if include_subclasses:
            for subclass in get_subclasses(model_class):
                classes.append(subclass)

        for _model_class in classes:
            if not issubclass(_model_class, Model):
                msg = 'Model class must be subclass of Model'
                raise TypeError(msg)

            qs = _model_class.objects.filter(
                _metadata__is_deleted=False,
                _address__object_version=Versions.ALL if all_versions else Versions.LATEST,
            )

            if all_versions:
                qs = qs.using(LAKEHOUSE_DB_ALIAS)

            if select_related:
                qs = qs.select_related(*select_related)

            if fields_restrictions:
                fields_restriction = fields_restrictions.get(_model_class.__name__, None)

                if fields_restriction:
                    qs = qs.only(fields_restriction.fields)

            if filters:
                # Resolve reference field filters (convert partition keys to objects)
                resolved_filters = cls._resolve_reference_filters(_model_class, filters)

                # Build filter kwargs - for 'eq', don't add __eq suffix (it's the default)
                filter_kwargs = {}
                for _filter in resolved_filters:
                    if _filter.filter_type.name == 'eq':
                        filter_kwargs[_filter.key] = _filter.target
                    else:
                        filter_kwargs[f'{_filter.key}__{_filter.filter_type.name}'] = _filter.target
                qs = qs.filter(Q(**filter_kwargs))

            total += qs.count().execute()

            is_optimized_file = model_class.__name__ == FILE_CLASS_NAME and file_optimized

            if is_optimized_file:
                _only = ['filename', 'size']

                qs = qs.only(_only)

            if ordering is None and all_versions:
                ordering = ['-_metadata__updated_at']

            if ordering:
                qs = qs.order_by(*ordering)

            if page_size is not None:
                offset = (page - 1) * page_size
                limit = offset + page_size

                qs = qs[offset:limit]

            items: list[Model] = qs.execute()

            for item in items:
                result.append(
                    await cls.build_object_data(
                        item,
                        base_url=base_url,
                        include_metadata=include_metadata,
                        fields_restrictions=fields_restrictions,
                        load_references=load_references,
                        is_file_object=is_optimized_file,
                        is_from_lakehouse=all_versions,
                    )
                )
        return result, total

    @classmethod
    async def _async_fetch_objects(
        cls,
        base_url: str,
        model_class: type[Model],
        filters: list[Filter],
        *,
        include_subclasses: bool = False,
        include_metadata: bool = False,
        fields_restrictions: dict[str, FieldsRestriction] | None = None,
        load_references: bool = False,
        all_versions: bool = False,
        file_optimized: bool = False,
        page: int = 1,
        page_size: int | None = None,
        ordering: list[str] | None = None,
        select_related: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        result: list[dict[str, Any]] = []
        total: int = 0
        classes: list[type[ModelBase]] = [model_class]

        if include_subclasses:
            for subclass in get_subclasses(model_class):
                classes.append(subclass)

        for _model_class in classes:
            if not issubclass(_model_class, Model):
                msg = 'Model class must be subclass of Model'
                raise TypeError(msg)

            qs = _model_class.objects.filter(
                _metadata__is_deleted=False,
                _address__object_version=Versions.ALL if all_versions else Versions.LATEST,
            )

            if all_versions:
                qs = qs.using(LAKEHOUSE_DB_ALIAS)

            if select_related:
                qs = qs.select_related(*select_related)

            if fields_restrictions:
                fields_restriction = fields_restrictions.get(_model_class.__name__, None)

                if fields_restriction:
                    qs = qs.only(fields_restriction.fields)

            if filters:
                # Resolve reference field filters (convert partition keys to objects)
                resolved_filters = cls._resolve_reference_filters(_model_class, filters)

                # Build filter kwargs - for 'eq', don't add __eq suffix (it's the default)
                filter_kwargs = {}
                for _filter in resolved_filters:
                    if _filter.filter_type.name == 'eq':
                        filter_kwargs[_filter.key] = _filter.target
                    else:
                        filter_kwargs[f'{_filter.key}__{_filter.filter_type.name}'] = _filter.target
                qs = qs.filter(Q(**filter_kwargs))

            total += await qs.count().aexecute()

            is_optimized_file = model_class.__name__ == FILE_CLASS_NAME and file_optimized

            if is_optimized_file:
                _only = ['filename', 'size']

                qs = qs.only(_only)

            if ordering is None and all_versions:
                ordering = ['-_metadata__updated_at']

            if ordering:
                qs = qs.order_by(*ordering)

            if page_size is not None:
                offset = (page - 1) * page_size
                limit = offset + page_size

                qs = qs[offset:limit]

            items: list[Model] = await qs.aexecute()

            for item in items:
                result.append(
                    await cls.build_object_data(
                        item,
                        base_url=base_url,
                        include_metadata=include_metadata,
                        fields_restrictions=fields_restrictions,
                        load_references=load_references,
                        is_file_object=is_optimized_file,
                        is_from_lakehouse=all_versions,
                    )
                )
        return result, total
