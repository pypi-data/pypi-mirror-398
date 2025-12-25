from amsdal_data.aliases.using import LAKEHOUSE_DB_ALIAS
from amsdal_models.classes.class_manager import ClassManager
from amsdal_models.classes.model import Model
from amsdal_models.querysets.base_queryset import QuerySet
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.models.enums import Versions
from amsdal_utils.query.utils import Q

from amsdal_server.apps.classes.errors import ClassNotFoundError


class ModelClassMixin:
    @classmethod
    def get_model_class_by_name(cls, class_name: str) -> type[Model]:
        class_item: Model | None = (
            cls.get_class_objects_qs().latest().filter(_address__object_id=class_name).first().execute()
        )

        if not class_item:
            msg = f'Class not found: {class_name}'
            raise ClassNotFoundError(class_name, msg)

        return cls.get_model_class(class_item)

    @classmethod
    async def async_get_model_class_by_name(cls, class_name: str) -> type[Model]:
        class_item: Model | None = (
            await cls.get_class_objects_qs().latest().filter(_address__object_id=class_name).first().aexecute()
        )

        if not class_item:
            msg = f'Class not found: {class_name}'
            raise ClassNotFoundError(class_name, msg)

        return cls.get_model_class(class_item)

    @classmethod
    def get_model_class(cls, class_item: Model) -> type[Model]:
        class_manager = ClassManager()
        model_class = class_manager.import_class(class_item.object_id)

        return model_class

    @classmethod
    def get_class_objects_qs(cls) -> QuerySet:  # type: ignore[type-arg]
        class_manager = ClassManager()
        class_object: type[Model] = class_manager.import_class('ClassObject', ModuleType.CORE)

        return class_object.objects.using(LAKEHOUSE_DB_ALIAS).filter(
            (Q(module_type=ModuleType.CONTRIB) | Q(module_type=ModuleType.USER) | Q(title='File')),  # ugly hack
            _metadata__is_deleted=False,
            _address__object_version=Versions.LATEST,
        )
