import httpx
from amsdal.cloud.constants import BASE_AUTH_URL as BASE_AUTH_URL
from amsdal.errors import AmsdalAuthConnectionError as AmsdalAuthConnectionError
from typing import Any, Protocol

class HttpFunction(Protocol):
    """
    Protocol for HTTP function callables.

    This protocol defines the structure for callables that perform HTTP requests, ensuring they accept a URL and
        additional keyword arguments.
    """
    def __call__(self, url: str, **kwargs: Any) -> httpx.Response: ...

class AuthClientService:
    """
    Service to handle HTTP requests for authentication.

    This class provides functionality to perform HTTP GET and POST requests to the authentication server,
    handling connection errors and setting default timeouts.
    """
    DEFAULT_TIMEOUT: int
    def _default_handler(self, calling_function: HttpFunction, path: str, **kwargs: Any) -> httpx.Response: ...
    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """
        Sends an HTTP POST request to the specified path.

        This method constructs the full URL using the base authentication URL and the provided path,
        sets a default timeout, and sends an HTTP POST request.

        Args:
            path (str): The path to append to the base authentication URL.
            **kwargs (Any): Additional keyword arguments to pass to the `httpx.post` function.

        Returns:
            httpx.Response: The response from the HTTP POST request.

        Raises:
            AmsdalAuthConnectionError: If there is a connection error.
        """
    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """
        Sends an HTTP GET request to the specified path.

        This method constructs the full URL using the base authentication URL and the provided path,
        sets a default timeout, and sends an HTTP GET request.

        Args:
            path (str): The path to append to the base authentication URL.
            **kwargs (Any): Additional keyword arguments to pass to the `httpx.get` function.

        Returns:
            httpx.Response: The response from the HTTP GET request.

        Raises:
            AmsdalAuthConnectionError: If there is a connection error.
        """
