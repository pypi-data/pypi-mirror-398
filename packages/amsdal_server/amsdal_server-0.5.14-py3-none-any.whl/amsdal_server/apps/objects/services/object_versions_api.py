from amsdal_models.classes.class_manager import ClassManager
from amsdal_models.classes.constants import FILE_CLASS_NAME
from amsdal_models.classes.errors import AmsdalClassError
from amsdal_models.classes.model import Model
from amsdal_models.querysets.executor import LAKEHOUSE_DB_ALIAS
from amsdal_models.schemas.object_schema import model_to_object_schema
from amsdal_utils.config.manager import AmsdalConfigManager
from amsdal_utils.models.data_models.address import Address
from starlette.authentication import BaseUser

from amsdal_server.apps.classes.errors import ClassNotFoundError
from amsdal_server.apps.classes.mixins.column_info_mixin import ColumnInfoMixin
from amsdal_server.apps.common.mixins.permissions_mixin import PermissionsMixin
from amsdal_server.apps.common.serializers.objects_response import ObjectsResponse
from amsdal_server.apps.objects.mixins.object_data_mixin import ObjectDataMixin
from amsdal_server.apps.objects.utils import apply_version_to_address


class ObjectVersionsApi(PermissionsMixin, ColumnInfoMixin, ObjectDataMixin):
    @classmethod
    async def get_object_versions(
        cls,
        user: BaseUser,
        base_url: str,
        address: str,
        version_id: str = '',
        *,
        all_versions: bool = False,
        include_metadata: bool = True,
        file_optimized: bool = False,
        select_related: list[str] | None = None,
    ) -> ObjectsResponse:
        if AmsdalConfigManager().get_config().async_mode:
            return await cls._aget_object_versions(
                user=user,
                base_url=base_url,
                address=address,
                version_id=version_id,
                all_versions=all_versions,
                include_metadata=include_metadata,
                file_optimized=file_optimized,
                select_related=select_related,
            )

        return await cls._get_object_versions(
            user=user,
            base_url=base_url,
            address=address,
            version_id=version_id,
            all_versions=all_versions,
            include_metadata=include_metadata,
            file_optimized=file_optimized,
            select_related=select_related,
        )

    @classmethod
    async def _get_object_versions(
        cls,
        user: BaseUser,
        base_url: str,
        address: str,
        version_id: str = '',
        *,
        all_versions: bool = False,
        include_metadata: bool = True,
        file_optimized: bool = False,
        select_related: list[str] | None = None,
    ) -> ObjectsResponse:
        _address = Address.from_string(address)

        try:
            model_class = ClassManager().import_class(_address.class_name)
        except (AmsdalClassError, ImportError) as e:
            raise ClassNotFoundError(_address.class_name) from e

        permissions_info = cls.get_permissions_info(model_class, user)
        class_properties = cls.get_class_properties(model_to_object_schema(model_class))

        result = ObjectsResponse(
            columns=class_properties,
            rows=[],
            total=0,
        )

        if permissions_info.has_read_permission:
            _address = apply_version_to_address(
                _address,
                version_id=version_id or _address.object_version,
                all_versions=all_versions,
            )

            qs = model_class.objects.filter(
                _metadata__is_deleted=False,
                _address__object_id=_address.object_id,
                _address__class_version=_address.class_version,
                _address__object_version=_address.object_version,
            )

            if all_versions:
                qs = qs.using(LAKEHOUSE_DB_ALIAS)

            if select_related:
                qs = qs.select_related(*select_related)

            is_optimized_file = model_class.__name__ == FILE_CLASS_NAME and file_optimized

            if is_optimized_file:
                qs = qs.only(['filename', 'size'])

            items: list[Model] = qs.order_by('-_metadata__updated_at').execute()

            for item in items:
                result.rows.append(
                    await cls.build_object_data(
                        item,
                        base_url=base_url,
                        include_metadata=include_metadata,
                        is_file_object=is_optimized_file,
                        is_from_lakehouse=all_versions,
                    ),
                )

        result.total = len(result.rows)

        return result

    @classmethod
    async def _aget_object_versions(
        cls,
        user: BaseUser,
        base_url: str,
        address: str,
        version_id: str = '',
        *,
        all_versions: bool = False,
        include_metadata: bool = True,
        file_optimized: bool = False,
        select_related: list[str] | None = None,
    ) -> ObjectsResponse:
        _address = Address.from_string(address)

        try:
            model_class = ClassManager().import_class(_address.class_name)
        except (AmsdalClassError, ImportError) as e:
            raise ClassNotFoundError(_address.class_name) from e

        permissions_info = await cls.async_get_permissions_info(model_class, user)
        class_properties = await cls.aget_class_properties(model_to_object_schema(model_class))

        result = ObjectsResponse(
            columns=class_properties,
            rows=[],
            total=0,
        )

        if permissions_info.has_read_permission:
            _address = apply_version_to_address(
                _address,
                version_id=version_id or _address.object_version,
                all_versions=all_versions,
            )
            qs = model_class.objects.filter(
                _metadata__is_deleted=False,
                _address__object_id=_address.object_id,
                _address__class_version=_address.class_version,
                _address__object_version=_address.object_version,
            )

            if all_versions:
                qs = qs.using(LAKEHOUSE_DB_ALIAS)

            if select_related:
                qs = qs.select_related(*select_related)

            is_optimized_file = model_class.__name__ == FILE_CLASS_NAME and file_optimized

            if is_optimized_file:
                qs = qs.only(['filename', 'size'])

            items: list[Model] = await qs.order_by('-_metadata__updated_at').aexecute()

            for item in items:
                result.rows.append(
                    await cls.build_object_data(
                        item,
                        base_url=base_url,
                        include_metadata=include_metadata,
                        is_file_object=is_optimized_file,
                        is_from_lakehouse=all_versions,
                    ),
                )

        result.total = len(result.rows)

        return result
