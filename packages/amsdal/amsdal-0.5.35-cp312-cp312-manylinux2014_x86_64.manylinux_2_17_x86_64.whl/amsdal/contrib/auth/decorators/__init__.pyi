from amsdal.context.manager import AmsdalContextManager as AmsdalContextManager
from amsdal.contrib.auth.errors import AuthenticationError as AuthenticationError
from collections.abc import Callable as Callable
from typing import Any

def require_auth(func: Callable[..., Any]) -> Callable[..., Any]: ...
