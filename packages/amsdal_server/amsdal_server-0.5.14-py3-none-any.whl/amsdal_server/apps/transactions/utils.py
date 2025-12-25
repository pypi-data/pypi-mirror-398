import ast

from amsdal_utils.config.manager import AmsdalConfigManager


def is_transaction(statement: ast.AST) -> bool:
    transaction_name = 'transaction'
    if AmsdalConfigManager().get_config().async_mode:
        transaction_name = 'async_transaction'

    if not isinstance(statement, ast.AsyncFunctionDef | ast.FunctionDef):
        return False

    if not statement.decorator_list:
        return False

    return any(
        decorator
        for decorator in statement.decorator_list
        if (
            (isinstance(decorator, ast.Name) and decorator.id in [transaction_name])
            or (
                isinstance(decorator, ast.Call)
                and isinstance(
                    decorator.func,
                    ast.Name,
                )
                and decorator.func.id in [transaction_name]
            )
        )
    )
