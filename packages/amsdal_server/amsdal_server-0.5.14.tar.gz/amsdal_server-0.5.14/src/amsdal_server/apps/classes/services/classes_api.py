from typing import Any

from amsdal_data.connections.historical.schema_version_manager import HistoricalSchemaVersionManager
from amsdal_models.classes.class_manager import ClassManager
from amsdal_models.classes.helpers.reference_loader import ReferenceLoader
from amsdal_models.classes.model import Model
from amsdal_models.migration.base_migration_schemas import DefaultMigrationSchemas
from amsdal_models.migration.executors.default_executor import DefaultMigrationExecutor
from amsdal_models.querysets.executor import LAKEHOUSE_DB_ALIAS
from amsdal_models.schemas.object_schema import model_to_object_schema
from amsdal_utils.config.manager import AmsdalConfigManager
from amsdal_utils.models.data_models.enums import MetaClasses
from amsdal_utils.models.enums import ModuleType
from amsdal_utils.schemas.schema import ObjectSchema
from amsdal_utils.schemas.schema import PropertyData
from starlette.authentication import BaseUser

from amsdal_server.apps.classes.errors import ClassNotFoundError
from amsdal_server.apps.classes.mixins.column_info_mixin import ColumnInfoMixin
from amsdal_server.apps.classes.mixins.model_class_info import ModelClassMixin
from amsdal_server.apps.classes.serializers.class_info import ClassInfo
from amsdal_server.apps.classes.serializers.register_class import ClassSchema
from amsdal_server.apps.classes.serializers.register_class import RegisterClassData
from amsdal_server.apps.common.errors import AmsdalPermissionError
from amsdal_server.apps.common.mixins.permissions_mixin import PermissionsMixin
from amsdal_server.apps.common.permissions.enums import AccessTypes
from amsdal_server.apps.objects.mixins.object_data_mixin import ObjectDataMixin


class ClassesApi(PermissionsMixin, ModelClassMixin, ColumnInfoMixin, ObjectDataMixin):
    @classmethod
    async def get_classes(cls, user: BaseUser) -> list[ClassInfo]:
        if AmsdalConfigManager().get_config().async_mode:
            return await cls._aget_classes(user)

        return await cls._get_classes(user)

    @classmethod
    async def _aget_classes(cls, user: BaseUser) -> list[ClassInfo]:
        classes: list[Model] = await cls.get_class_objects_qs().aexecute()
        result: list[ClassInfo] = []

        for class_item in classes:
            result.append(await cls.get_class(user, class_item))

        return result

    @classmethod
    async def _get_classes(cls, user: BaseUser) -> list[ClassInfo]:
        classes: list[Model] = cls.get_class_objects_qs().filter().execute()
        result: list[ClassInfo] = []

        for class_item in classes:
            result.append(await cls.get_class(user, class_item))

        return result

    @classmethod
    async def get_class_by_name(
        cls,
        user: BaseUser,
        class_name: str,
    ) -> ClassInfo:
        class_item: Model | None
        if AmsdalConfigManager().get_config().async_mode:
            class_item = await cls.get_class_objects_qs().filter(_address__object_id=class_name).first().aexecute()
        else:
            class_item = cls.get_class_objects_qs().filter(_address__object_id=class_name).first().execute()

        if not class_item:
            msg = f'Class not found: {class_name}'
            raise ClassNotFoundError(class_name, msg)

        return await cls.get_class(user, class_item)

    @classmethod
    async def get_class(
        cls,
        user: BaseUser,
        class_item: Model,
    ) -> ClassInfo:
        if AmsdalConfigManager().get_config().async_mode:
            return await cls._aget_class(user, class_item)

        return await cls._get_class(user, class_item)

    @classmethod
    async def _aget_class(
        cls,
        user: BaseUser,
        class_item: Model,
    ) -> ClassInfo:
        model_class = cls.get_model_class(class_item)

        try:
            permissions_info = await cls.async_get_permissions_info(model_class, user)
            has_read_permission = permissions_info.has_read_permission
        except AmsdalPermissionError:
            has_read_permission = False

        class_properties = await cls.aget_class_properties_by_class_and_meta(class_item)
        data: dict[str, Any] = {
            'class': class_item.object_id,
            'count': 0,
            'properties': class_properties,
        }
        class_info = ClassInfo(**data)

        if has_read_permission:
            class_info.count = await model_class.objects.latest().filter(_metadata__is_deleted=False).count().aexecute()

        return class_info

    @classmethod
    async def _get_class(
        cls,
        user: BaseUser,
        class_item: Model,
    ) -> ClassInfo:
        model_class = cls.get_model_class(class_item)

        try:
            permissions_info = cls.get_permissions_info(model_class, user)
            has_read_permission = permissions_info.has_read_permission
        except AmsdalPermissionError:
            has_read_permission = False

        class_properties = cls.get_class_properties_by_class_object(class_item)
        data: dict[str, Any] = {
            'class': class_item.object_id,
            'count': 0,
            'properties': class_properties,
        }
        class_info = ClassInfo(**data)

        if has_read_permission:
            class_info.count = model_class.objects.latest().filter(_metadata__is_deleted=False).count().execute()

        return class_info

    @classmethod
    def register_class(
        cls,
        user: BaseUser,
        data: RegisterClassData,
        *,
        skip_data_migrations: bool = False,  # noqa: ARG003
    ) -> ClassInfo:
        # TODO: rewrite this completely
        from amsdal.models.core.class_object import ClassObject
        from amsdal.models.core.class_object_meta import ClassObjectMeta  # type: ignore[import-not-found]

        permissions_info = cls.get_permissions_info(
            ClassObjectMeta,
            user,
            [AccessTypes.CREATE, AccessTypes.UPDATE],
        )
        object_schema = cls._build_object_schema(data.class_schema)

        model_object = (
            ClassObjectMeta.objects.using(LAKEHOUSE_DB_ALIAS)
            .latest()
            .filter(
                _metadata__is_deleted=False,
                title=data.class_schema.title,
            )
            .first()
            .execute()
        )

        if model_object:
            if not permissions_info.has_update_permission:
                raise AmsdalPermissionError(
                    access_type=AccessTypes.UPDATE,
                    class_name=ClassObjectMeta.__name__,
                )
        elif not permissions_info.has_create_permission:
            raise AmsdalPermissionError(
                access_type=AccessTypes.CREATE,
                class_name=ClassObjectMeta.__name__,
            )

        cls._generate_model_class(object_schema)
        migration_schemas = DefaultMigrationSchemas()
        migrartion_executor = DefaultMigrationExecutor(migration_schemas)
        class_name = object_schema.title

        _props: dict[str, dict[str, Any]] = {}
        _props_meta: dict[str, dict[str, Any]] = {}
        if object_schema.properties:
            _props = {
                p_name: {
                    'type': p_value.type,
                    'items': p_value.items,
                }
                for p_name, p_value in object_schema.properties.items()
            }
            _props_meta = {
                p_name: {
                    'title': p_value.title,
                    'default': p_value.default,
                    'options': p_value.options,
                }
                for p_name, p_value in object_schema.properties.items()
            }
            for p_name, p_value in object_schema.properties.items():
                p_value.field_name = p_name
                p_value.field_id = p_name

        if not model_object:
            class_object_object = ClassObject(  # type: ignore[call-arg]
                properties=_props,  # type: ignore[arg-type]
                required=object_schema.required,
                meta_class=MetaClasses.CLASS_OBJECT,
                _object_id=class_name,
            )
            class_object_object.save(force_insert=True)
            HistoricalSchemaVersionManager().register_last_version(
                class_name,
                class_object_object.get_metadata().address.object_version,
            )
            migrartion_executor._create_table(object_schema, class_object_object.get_metadata().address.object_version)
            class_object_meta_object = ClassObjectMeta(
                title=class_name,
                type=object_schema.type,
                properties=_props_meta,
                indexed=object_schema.indexed,  # type: ignore[attr-defined]
                unique=object_schema.unique,  # type: ignore[attr-defined]
                custom_code=object_schema.custom_code,
                _object_id=class_name,
            )
            class_object_meta_object.save(force_insert=True)

        else:
            class_object_object = ReferenceLoader(  # type: ignore[assignment]
                model_object.get_metadata().class_meta_schema_reference
            ).load_reference(using=LAKEHOUSE_DB_ALIAS)

            if class_object_object.properties != _props:
                class_object_object.properties = _props  # type: ignore[assignment]
                class_object_object.save()
                HistoricalSchemaVersionManager().register_last_version(
                    class_name,
                    class_object_object.get_metadata().address.object_version,
                )
                migrartion_executor._create_table(
                    object_schema, class_object_object.get_metadata().address.object_version
                )
                model_object.title = class_name
                model_object.type = object_schema.type
                model_object.properties = _props_meta
                model_object.indexed = object_schema.indexed  # type: ignore[attr-defined]
                model_object.unique = object_schema.unique  # type: ignore[attr-defined]
                model_object.custom_code = object_schema.custom_code
                model_object.save()
                migration_schemas._classes[class_name] = ClassManager().import_class(class_name, ModuleType.USER)
                migrartion_executor._migrate_historical_data(  # type: ignore[attr-defined]
                    migrartion_executor.schemas,
                    class_name,
                    prior_version=class_object_object.get_metadata().prior_version,
                    new_version=class_object_object.get_metadata().address.object_version,
                )

        class_properties = cls.get_class_properties(object_schema)
        class_info = ClassInfo(
            **{  # type: ignore[arg-type]
                'class': object_schema.title,
                'count': 0,  # TODO: get count
                'properties': class_properties,
            },
        )

        return class_info

    @classmethod
    def unregister_class(
        cls,
        user: BaseUser,
        class_name: str,
    ) -> None:
        from amsdal.models.core.class_object import ClassObject

        permissions_info = cls.get_permissions_info(
            ClassObject,
            user,
            [AccessTypes.DELETE],
        )

        if not permissions_info.has_update_permission:
            raise AmsdalPermissionError(
                access_type=AccessTypes.DELETE,
                class_name=ClassObject.__name__,
            )

        class_object = (
            ClassObject.objects.latest()
            .filter(
                title=class_name,
                _metadata__is_deleted=False,
            )
            .first()
            .execute()
        )

        if class_object:
            class_object.get_metadata().is_deleted = True
            class_object.save()

    @classmethod
    def _build_object_schema(cls, class_schema: ClassSchema) -> ObjectSchema:
        try:
            _model = ClassManager().import_class(class_schema.title)
            return model_to_object_schema(_model)
        except ImportError:
            pass

        return ObjectSchema(  # type: ignore[call-arg]
            title=class_schema.title,
            type=class_schema.type,
            properties={
                property_name: PropertyData(**property_data.model_dump())
                for property_name, property_data in class_schema.properties.items()
            },
            required=class_schema.required,
            indexed=class_schema.indexed,
            unique=class_schema.unique,
            custom_code=class_schema.custom_code,
        )

    @classmethod
    def _generate_model_class(cls, schema: ObjectSchema) -> None:
        pass
