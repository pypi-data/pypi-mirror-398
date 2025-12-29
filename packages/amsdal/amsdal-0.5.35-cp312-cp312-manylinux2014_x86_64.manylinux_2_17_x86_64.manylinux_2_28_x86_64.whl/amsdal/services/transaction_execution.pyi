import ast
from _typeshed import Incomplete
from amsdal.configs.main import settings as settings
from amsdal.errors import TransactionNotFoundError as TransactionNotFoundError
from amsdal_utils.utils.singleton import Singleton
from collections.abc import Callable as Callable, Generator
from pathlib import Path
from typing import Any

logger: Incomplete

def is_transaction(statement: ast.AST) -> bool:
    """
    Determines if a given AST statement is a transaction function.

    This function checks if the provided AST statement is an asynchronous or synchronous function
    definition that is decorated with the `transaction` decorator.

    Args:
        statement (ast.AST): The AST statement to check.

    Returns:
        bool: True if the statement is a transaction function, False otherwise.
    """
def annotation_is_model(annotation: Any) -> bool: ...

class TransactionExecutionService(metaclass=Singleton):
    """
    Service for executing transactions.

    This class provides methods to execute transactions, load transaction functions,
    and handle asynchronous transactions. It ensures that transactions are executed
    with the correct arguments and handles any necessary preprocessing of arguments.
    """
    _transactions: dict[str, Callable[..., Any]]
    def __init__(self) -> None: ...
    def execute_transaction(self, transaction_name: str, args: dict[str, Any], *, load_references: bool = True) -> Any:
        """
        Executes a transaction with the given name and arguments.

        This method retrieves the transaction function by its name, processes the arguments,
        and executes the transaction. It handles both synchronous and asynchronous transactions
        and performs necessary preprocessing of arguments, such as loading references.

        Args:
            transaction_name (str): The name of the transaction to execute.
            args (dict[str, Any]): The arguments to pass to the transaction function.
            load_references (bool, optional): Whether to load references in the arguments. Defaults to True.

        Returns:
            Any: The result of the transaction execution.
        """
    async def async_execute_transaction(self, transaction_name: str, args: dict[str, Any], *, load_references: bool = True) -> Any:
        """
        Executes a transaction with the given name and arguments.

        This method retrieves the transaction function by its name, processes the arguments,
        and executes the transaction. It handles both synchronous and asynchronous transactions
        and performs necessary preprocessing of arguments, such as loading references.

        Args:
            transaction_name (str): The name of the transaction to execute.
            args (dict[str, Any]): The arguments to pass to the transaction function.
            load_references (bool, optional): Whether to load references in the arguments. Defaults to True.

        Returns:
            Any: The result of the transaction execution.
        """
    def get_transaction_func(self, transaction_name: str) -> Callable[..., Any]:
        """
        Retrieves the transaction function by its name.

        This method checks if the transaction function is already loaded in the `_transactions` dictionary.
        If not, it attempts to load the transaction function from the available transaction definitions.

        Args:
            transaction_name (str): The name of the transaction function to retrieve.

        Returns:
            Callable[..., Any]: The transaction function corresponding to the given name.

        Raises:
            TransactionNotFoundError: If the transaction function with the specified name is not found.
        """
    @staticmethod
    def _run_async_transaction(transaction_func: Callable[..., Any], args: dict[str, Any]) -> Any: ...
    def _load_transaction(self, transaction_name: str) -> Callable[..., Any]: ...
    @classmethod
    def _get_transaction_definitions(cls) -> Generator[tuple[ast.FunctionDef | ast.AsyncFunctionDef, Path], None, None]: ...
    @classmethod
    def _iterate_module(cls, module_path: Path) -> Generator[tuple[ast.FunctionDef | ast.AsyncFunctionDef, Path], None, None]: ...
    @classmethod
    def _iterate_file(cls, file_path: Path) -> Generator[tuple[ast.FunctionDef | ast.AsyncFunctionDef, Path], None, None]: ...
