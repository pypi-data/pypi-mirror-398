import ast
import types
from collections.abc import Generator
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any

from amsdal.configs.main import settings
from amsdal.contrib.frontend_configs.conversion.convert import convert_to_frontend_config
from amsdal_utils.models.data_models.enums import CoreTypes

from amsdal_server.apps.transactions.serializers.transaction_item import TransactionItemSerializer
from amsdal_server.apps.transactions.serializers.transaction_property import DictTypeSerializer
from amsdal_server.apps.transactions.serializers.transaction_property import TransactionPropertySerializer
from amsdal_server.apps.transactions.serializers.transaction_property import TypeSerializer
from amsdal_server.apps.transactions.utils import is_transaction


class AstParserMixin:
    @classmethod
    def _get_transaction_definitions(cls) -> Generator[tuple[ast.FunctionDef | ast.AsyncFunctionDef, Path], None, None]:
        # Scan main transactions path
        transactions_path: Path = cls._get_transactions_path()
        yield from cls._iterate_module(transactions_path)

        # Scan contrib module transaction paths
        for contrib_path in cls._get_contrib_transaction_paths():
            yield from cls._iterate_module(contrib_path)

    @classmethod
    def _iterate_module(
        cls, module_path: Path
    ) -> Generator[tuple[ast.FunctionDef | ast.AsyncFunctionDef, Path], None, None]:
        if not module_path.exists():
            return

        elif module_path.is_dir():
            for file in module_path.iterdir():
                yield from cls._iterate_module(file)
        elif module_path.suffix == '.py':
            yield from cls._iterate_file(module_path)

    @classmethod
    def _iterate_file(
        cls, file_path: Path
    ) -> Generator[tuple[ast.FunctionDef | ast.AsyncFunctionDef, Path], None, None]:
        transactions_content = file_path.read_text()
        tree = ast.parse(transactions_content)

        for definition in ast.walk(tree):
            if not is_transaction(definition):
                continue

            yield definition, file_path  # type: ignore[misc]

    @classmethod
    def build_transaction_item(
        cls,
        definition: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> TransactionItemSerializer:
        transaction_item = TransactionItemSerializer(
            title=definition.name,
            properties={},
        )

        for arg in definition.args.args:
            if hasattr(arg.annotation, 'id'):
                transaction_item.properties[arg.arg] = TransactionPropertySerializer(
                    title=arg.arg,
                    type=cls._normalize_type(arg.annotation.id),  # type: ignore[union-attr]
                )
            elif hasattr(arg.annotation, 'value'):
                if arg.annotation.value.id.lower() == 'list':  # type: ignore[union-attr]
                    transaction_item.properties[arg.arg] = TransactionPropertySerializer(
                        title=arg.arg,
                        type=CoreTypes.ARRAY.value,
                        items=TypeSerializer(
                            type=cls._normalize_type(arg.annotation.slice.id),  # type: ignore[union-attr]
                        ),
                    )
                elif arg.annotation.value.id.lower() == 'dict':  # type: ignore[union-attr]
                    transaction_item.properties[arg.arg] = TransactionPropertySerializer(
                        title=arg.arg,
                        type=CoreTypes.DICTIONARY.value,
                        items=DictTypeSerializer(
                            key=TypeSerializer(
                                type=cls._normalize_type(arg.annotation.slice.elts[0].id),  # type: ignore[union-attr]
                            ),
                            value=TypeSerializer(
                                type=cls._normalize_type(arg.annotation.slice.elts[1].id),  # type: ignore[union-attr]
                            ),
                        ),
                    )
                elif arg.annotation.value.id.lower() == 'optional':  # type: ignore[union-attr]
                    transaction_item.properties[arg.arg] = TransactionPropertySerializer(
                        title=arg.arg,
                        type=CoreTypes.ANYTHING.value,
                    )
                else:
                    msg = 'Error parsing annotation with value and no id attribute is not expected...'
                    raise ValueError(msg)
            else:
                transaction_item.properties[arg.arg] = TransactionPropertySerializer(
                    title=arg.arg,
                    type=CoreTypes.ANYTHING.value,
                )

        return transaction_item

    @classmethod
    def _get_transactions_path(cls) -> Path:
        return settings.transactions_root_path

    @classmethod
    def _get_contrib_transaction_paths(cls) -> Generator[Path, None, None]:
        """
        Yields transaction directories from installed contrib modules.

        This method iterates through the configured contrib modules and yields
        their transaction directories if they exist.
        """
        import importlib

        for contrib_config in settings.CONTRIBS:
            # Extract package name from config (e.g., 'amsdal.contrib.auth.app.AuthAppConfig')
            # by removing '.app.ConfigClass' suffix
            package_name = contrib_config.rsplit('.', 2)[0]

            try:
                contrib_module = importlib.import_module(package_name)
                if hasattr(contrib_module, '__path__'):
                    contrib_package_path = Path(contrib_module.__path__[0])
                    transactions_path = contrib_package_path / 'transactions'

                    if transactions_path.exists() and transactions_path.is_dir():
                        yield transactions_path
            except ImportError:
                continue

    @classmethod
    def _normalize_type(cls, json_or_py_type: str) -> str:
        json_switcher = {
            CoreTypes.STRING.value: 'str',
            CoreTypes.NUMBER.value: 'float',
            CoreTypes.ANYTHING.value: 'Any',
            CoreTypes.BOOLEAN.value: 'bool',
            CoreTypes.BINARY.value: 'bytes',
            CoreTypes.ARRAY.value: 'list',
        }
        py_switcher = {
            'str': CoreTypes.STRING.value,
            'int': CoreTypes.NUMBER.value,
            'float': CoreTypes.NUMBER.value,
            'Any': CoreTypes.ANYTHING.value,
            'bool': CoreTypes.BOOLEAN.value,
            'bytes': CoreTypes.BINARY.value,
            'List': CoreTypes.ARRAY.value,
            'list': CoreTypes.ARRAY.value,
        }

        return json_switcher.get(json_or_py_type, py_switcher.get(json_or_py_type, json_or_py_type))

    @classmethod
    def build_frontend_control(
        cls,
        definition: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: Path,
    ) -> dict[str, Any]:
        loader = SourceFileLoader(file_path.stem, str(file_path.absolute()))
        transaction_module = types.ModuleType(loader.name)
        loader.exec_module(transaction_module)
        transaction_function = getattr(transaction_module, definition.name)

        return convert_to_frontend_config(transaction_function)
