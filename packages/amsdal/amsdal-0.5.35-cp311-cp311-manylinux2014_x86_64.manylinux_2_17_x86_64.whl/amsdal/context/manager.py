from contextvars import ContextVar
from typing import Any

_CONTEXT: ContextVar[dict[str, Any] | None] = ContextVar('_context', default=None)


class AmsdalContextManager:
    """
    Manages a context for storing and retrieving data.

    This class provides methods to get, set, and add to a context stored in a
    `ContextVar`. The context is a dictionary that can hold any key-value pairs.
    """

    @classmethod
    def get_context(cls) -> dict[str, Any]:
        """
        Retrieves the current context or creates a new one if none exists.

        This method gets the current context from the `_CONTEXT` variable. If no
        context exists, it creates a new empty context and sets it.

        Returns:
            dict[str, Any]: The current context.
        """
        _context = _CONTEXT.get()

        if _context is not None:
            return _context

        new_context: dict[str, Any] = {}
        cls.set_context(new_context)

        return new_context

    @classmethod
    def set_context(cls, context: dict[str, Any]) -> None:
        """
        Sets the context to the provided dictionary.

        This method sets the `_CONTEXT` variable to the provided context.

        Args:
            context (dict[str, Any]): The context to set.

        Returns:
            None
        """
        _CONTEXT.set(context)

    @classmethod
    def add_to_context(cls, key: str, value: Any) -> None:
        """
        Adds a key-value pair to the current context.

        This method adds the provided key-value pair to the current context.

        Args:
            key (str): The key to add to the context.
            value (Any): The value to associate with the key.

        Returns:
            None
        """
        context = cls.get_context()

        context[key] = value

        cls.set_context(context)
