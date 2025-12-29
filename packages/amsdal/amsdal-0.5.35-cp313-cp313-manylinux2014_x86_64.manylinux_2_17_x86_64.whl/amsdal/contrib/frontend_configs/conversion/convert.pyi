from _typeshed import Incomplete
from types import UnionType
from typing import Any

default_types_map: Incomplete

def _process_union(value: UnionType, *, is_transaction: bool = False) -> dict[str, Any]: ...
def convert_to_frontend_config(value: Any, *, is_transaction: bool = False) -> dict[str, Any]:
    """
    Converts a given value to a frontend configuration dictionary.

    This function takes a value and converts it into a dictionary that represents
    the configuration for a frontend form control. It handles various types such as
    Union, list, dict, BaseModel, and custom types.

    Args:
        value (Any): The value to be converted to frontend configuration.
        is_transaction (bool, optional): Indicates if the conversion is for a transaction. Defaults to False.

    Returns:
        dict[str, Any]: A dictionary representing the frontend configuration for the given value.
    """
