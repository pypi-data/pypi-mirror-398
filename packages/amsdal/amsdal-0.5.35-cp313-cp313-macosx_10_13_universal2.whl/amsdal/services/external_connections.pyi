from _typeshed import Incomplete
from amsdal_data.application import AsyncDataApplication, DataApplication
from amsdal_utils.utils.singleton import Singleton
from typing import Any, TypeVar

T = TypeVar('T')

class ExternalConnectionManager(metaclass=Singleton):
    """
    Manager for accessing external service connections.

    Provides a convenient interface to access external connections configured
    in the application, such as read-only databases, email services, etc.

    Example usage:
        manager = ExternalConnectionManager()

        # Get read-only database connection
        external_db = manager.get_connection('external_users_db')
        rows = external_db.fetch_all('SELECT * FROM users WHERE active = 1')

        # Get email service
        email = manager.get_connection('email_service')
        email.send_email(...)
    """
    _data_application: DataApplication | None
    _async_data_application: AsyncDataApplication | None
    def __init__(self) -> None: ...
    def setup(self, data_application: DataApplication | None = None, async_data_application: AsyncDataApplication | None = None) -> None:
        """
        Set up the manager with the data application instance.

        Args:
            data_application: Sync DataApplication instance
            async_data_application: Async DataApplication instance
        """
    def get_connection(self, name: str) -> Any:
        """
        Get an external service connection by name.

        Args:
            name: Name of the external connection (as configured in resources)

        Returns:
            The external connection object

        Raises:
            RuntimeError: If manager is not set up
            KeyError: If connection not found
        """
    def has_connection(self, name: str) -> bool:
        """
        Check if an external connection exists.

        Args:
            name: Name of the external connection

        Returns:
            bool: True if connection exists, False otherwise
        """
    def list_connections(self) -> list[str]:
        """
        List all available external connection names.

        Returns:
            list[str]: List of connection names
        """

class ExternalDatabaseReader:
    """
    Helper class for reading from external read-only databases.

    Provides a convenient interface for querying external databases
    with common patterns like filtering, mapping results, etc.

    Example usage:
        reader = ExternalDatabaseReader('external_users_db')

        # Fetch all users
        users = reader.fetch_all('SELECT * FROM users')

        # Fetch with parameters
        active_users = reader.fetch_all(
            'SELECT * FROM users WHERE active = ?',
            (1,)
        )

        # Fetch one record
        user = reader.fetch_one('SELECT * FROM users WHERE id = ?', (user_id,))

        # Get as dictionaries
        user_dicts = reader.fetch_all_as_dicts('SELECT * FROM users LIMIT 10')
    """
    connection_name: Incomplete
    _manager: Incomplete
    def __init__(self, connection_name: str) -> None:
        """
        Initialize the reader with a connection name.

        Args:
            connection_name: Name of the external database connection
        """
    @property
    def connection(self) -> Any:
        """Get the underlying connection object."""
    def fetch_all(self, query: str, parameters: tuple[Any, ...] | None = None) -> list[Any]:
        """
        Execute query and fetch all results.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            list: List of result rows
        """
    def fetch_one(self, query: str, parameters: tuple[Any, ...] | None = None) -> Any | None:
        """
        Execute query and fetch one result.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            Single result row or None
        """
    def fetch_all_as_dicts(self, query: str, parameters: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        """
        Execute query and fetch all results as dictionaries.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            list[dict]: List of result dictionaries
        """
    def fetch_one_as_dict(self, query: str, parameters: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        """
        Execute query and fetch one result as dictionary.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            dict | None: Result dictionary or None
        """
    def get_table_names(self) -> list[str]:
        """
        Get list of all tables in the database.

        Returns:
            list[str]: List of table names
        """
    def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        """
        Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            list[dict]: List of column information dictionaries
        """
    def count(self, table: str, where_clause: str = '', parameters: tuple[Any, ...] | None = None) -> int:
        """
        Count rows in a table.

        Args:
            table: Table name
            where_clause: Optional WHERE clause (without WHERE keyword)
            parameters: Query parameters for WHERE clause

        Returns:
            int: Number of rows
        """
    def exists(self, table: str, where_clause: str, parameters: tuple[Any, ...]) -> bool:
        """
        Check if a record exists.

        Args:
            table: Table name
            where_clause: WHERE clause (without WHERE keyword)
            parameters: Query parameters

        Returns:
            bool: True if record exists, False otherwise
        """
