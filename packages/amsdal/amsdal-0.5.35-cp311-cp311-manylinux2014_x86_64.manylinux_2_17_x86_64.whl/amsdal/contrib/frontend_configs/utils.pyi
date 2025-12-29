from typing import Any

def merge_ui_configs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Merges two UI configs together. The override config will take precedence over the base config.

    This function recursively merges two dictionaries representing UI configurations.
    If a key exists in both dictionaries, the value from the override dictionary will be used.
    If the value is a dictionary or a list, the function will merge them recursively.

    Args:
        base (dict[str, Any]): The base UI configuration dictionary.
        override (dict[str, Any]): The override UI configuration dictionary.

    Returns:
        dict[str, Any]: The merged UI configuration dictionary.
    """
