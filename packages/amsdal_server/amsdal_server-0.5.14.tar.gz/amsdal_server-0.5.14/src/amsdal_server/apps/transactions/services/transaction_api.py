from amsdal_utils.models.data_models.enums import CoreTypes
from amsdal_utils.models.data_models.enums import MetaClasses
from amsdal_utils.schemas.schema import ObjectSchema
from amsdal_utils.schemas.schema import PropertyData

from amsdal_server.apps.classes.errors import TransactionNotFoundError
from amsdal_server.apps.classes.mixins.column_info_mixin import ColumnInfoMixin
from amsdal_server.apps.common.serializers.column_response import ColumnInfo
from amsdal_server.apps.common.serializers.objects_response import ObjectsResponse
from amsdal_server.apps.common.serializers.objects_response import ObjectsResponseControl
from amsdal_server.apps.transactions.mixins.ast_parser_mixin import AstParserMixin


class TransactionApi(AstParserMixin, ColumnInfoMixin):
    @classmethod
    def get_transactions(cls) -> ObjectsResponse:
        result = ObjectsResponse(
            columns=cls.get_transaction_properties(),
            total=0,
            rows=[],
        )

        for definition, _ in cls._get_transaction_definitions():
            result.rows.append(cls.build_transaction_item(definition))

        result.total = len(result.rows)

        return result

    @classmethod
    def get_transaction(cls, transaction_name: str) -> ObjectsResponseControl:
        result = ObjectsResponseControl(
            columns=cls.get_transaction_properties(),
            rows=[],
            control={},
        )
        for definition, file_path in cls._get_transaction_definitions():
            if transaction_name != definition.name:
                continue

            result.rows.append(cls.build_transaction_item(definition))
            result.control = cls.build_frontend_control(definition, file_path)

        if not result.rows:
            raise TransactionNotFoundError(transaction_name)

        return result

    @classmethod
    def get_transaction_properties(cls) -> list[ColumnInfo]:
        transaction_schema = ObjectSchema(
            title='TransactionScreen',
            type='object',
            properties={
                'transaction': PropertyData(
                    type=CoreTypes.STRING.value,
                    items=None,
                    title='TransactionName',
                    read_only=False,
                    options=None,
                    default=None,
                    field_name='transaction',
                    field_id=None,
                    is_deleted=False,
                ),
                'args': PropertyData(
                    type=CoreTypes.ANYTHING.value,
                    items=None,
                    title='Args',
                    read_only=False,
                    options=None,
                    default=None,
                    field_name='args',
                    field_id=None,
                    is_deleted=False,
                ),
            },
            required=[],
            options=None,
            meta_class=MetaClasses.CLASS_OBJECT.value,
            custom_code=None,
            default=None,
        )

        return cls.get_class_properties(transaction_schema)
