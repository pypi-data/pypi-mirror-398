import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any

from amsdal.context.manager import AmsdalContextManager
from amsdal.contrib.auth.errors import AuthenticationError


def require_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Callable[..., Any]:
            request = AmsdalContextManager().get_context().get('request', None)

            if not request or not request.user:
                msg = 'Authentication required'
                raise AuthenticationError(msg)

            return await func(*args, **kwargs)

    else:

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Callable[..., Any]:
            request = AmsdalContextManager().get_context().get('request', None)

            if not request or not request.user:
                msg = 'Authentication required'
                raise AuthenticationError(msg)

            return func(*args, **kwargs)

    return wrapper
