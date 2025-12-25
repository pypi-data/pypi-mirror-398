from amsdal_models.classes.constants import FILE_CLASS_NAME
from amsdal_models.classes.model import Model
from amsdal_models.querysets.executor import LAKEHOUSE_DB_ALIAS
from amsdal_utils.config.manager import AmsdalConfigManager
from starlette.authentication import BaseUser

from amsdal_server.apps.classes.mixins.model_class_info import ModelClassMixin
from amsdal_server.apps.common.mixins.permissions_mixin import PermissionsMixin


class ObjectFileApi(PermissionsMixin, ModelClassMixin):
    @classmethod
    async def get_file(cls, user: BaseUser, object_id: str, object_version: str) -> Model | None:
        if AmsdalConfigManager().get_config().async_mode:
            return await cls._aget_file(user, object_id, object_version)

        return cls._get_file(user, object_id, object_version)

    @classmethod
    async def _aget_file(cls, user: BaseUser, object_id: str, object_version: str) -> Model | None:
        model_class = await cls.async_get_model_class_by_name(FILE_CLASS_NAME)
        permissions_info = await cls.async_get_permissions_info(model_class, user)

        if not permissions_info.has_read_permission:
            return None

        qs = model_class.objects.filter(_address__object_id=object_id)

        if object_version:
            qs = qs.using(LAKEHOUSE_DB_ALIAS).filter(_address__object_version=object_version)

        obj = await qs.get_or_none().aexecute()

        if obj:
            permissions_info = await cls.async_get_permissions_info(model_class, user, obj=obj)

            if not permissions_info.has_read_permission:
                return None

        return obj

    @classmethod
    def _get_file(cls, user: BaseUser, object_id: str, object_version: str) -> Model | None:
        model_class = cls.get_model_class_by_name(FILE_CLASS_NAME)
        permissions_info = cls.get_permissions_info(model_class, user)

        if not permissions_info.has_read_permission:
            return None

        qs = model_class.objects.filter(_address__object_id=object_id)

        if object_version:
            qs = qs.using(LAKEHOUSE_DB_ALIAS).filter(_address__object_version=object_version)

        obj = qs.get_or_none().execute()

        if obj:
            permissions_info = cls.get_permissions_info(model_class, user, obj=obj)

            if not permissions_info.has_read_permission:
                return None

        return obj
