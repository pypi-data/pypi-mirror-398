"""
External Connection Manager for accessing external services and databases.

This module provides a high-level interface for working with external connections
such as read-only databases, email services, storage services, etc.
"""

from typing import Any
from typing import TypeVar

from amsdal_data.application import AsyncDataApplication
from amsdal_data.application import DataApplication
from amsdal_utils.utils.singleton import Singleton

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

    def __init__(self) -> None:
        self._data_application: DataApplication | None = None
        self._async_data_application: AsyncDataApplication | None = None

    def setup(
        self,
        data_application: DataApplication | None = None,
        async_data_application: AsyncDataApplication | None = None,
    ) -> None:
        """
        Set up the manager with the data application instance.

        Args:
            data_application: Sync DataApplication instance
            async_data_application: Async DataApplication instance
        """
        self._data_application = data_application
        self._async_data_application = async_data_application

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
        if self._data_application is None and self._async_data_application is None:
            msg = 'ExternalConnectionManager not set up. Call setup() first.'
            raise RuntimeError(msg)

        app = self._data_application or self._async_data_application
        if app is None:  # Shouldn't happen due to check above, but satisfy mypy
            msg = 'No data application available'
            raise RuntimeError(msg)
        return app.get_external_service_connection(name)

    def has_connection(self, name: str) -> bool:
        """
        Check if an external connection exists.

        Args:
            name: Name of the external connection

        Returns:
            bool: True if connection exists, False otherwise
        """
        if self._data_application is None and self._async_data_application is None:
            return False

        try:
            self.get_connection(name)
            return True
        except KeyError:
            return False

    def list_connections(self) -> list[str]:
        """
        List all available external connection names.

        Returns:
            list[str]: List of connection names
        """
        if self._data_application:
            return list(self._data_application._external_service_connections.keys())  # noqa: SLF001
        if self._async_data_application:
            return list(self._async_data_application._external_service_connections.keys())  # noqa: SLF001
        return []


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

    def __init__(self, connection_name: str):
        """
        Initialize the reader with a connection name.

        Args:
            connection_name: Name of the external database connection
        """
        self.connection_name = connection_name
        self._manager = ExternalConnectionManager()

    @property
    def connection(self) -> Any:
        """Get the underlying connection object."""
        return self._manager.get_connection(self.connection_name)

    def fetch_all(self, query: str, parameters: tuple[Any, ...] | None = None) -> list[Any]:
        """
        Execute query and fetch all results.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            list: List of result rows
        """
        return self.connection.fetch_all(query, parameters)

    def fetch_one(self, query: str, parameters: tuple[Any, ...] | None = None) -> Any | None:
        """
        Execute query and fetch one result.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            Single result row or None
        """
        return self.connection.fetch_one(query, parameters)

    def fetch_all_as_dicts(self, query: str, parameters: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        """
        Execute query and fetch all results as dictionaries.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            list[dict]: List of result dictionaries
        """
        rows = self.fetch_all(query, parameters)
        return [dict(row) for row in rows]

    def fetch_one_as_dict(self, query: str, parameters: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        """
        Execute query and fetch one result as dictionary.

        Args:
            query: SQL query to execute
            parameters: Query parameters (optional)

        Returns:
            dict | None: Result dictionary or None
        """
        row = self.fetch_one(query, parameters)
        return dict(row) if row else None

    def get_table_names(self) -> list[str]:
        """
        Get list of all tables in the database.

        Returns:
            list[str]: List of table names
        """
        return self.connection.get_table_names()

    def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        """
        Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            list[dict]: List of column information dictionaries
        """
        return self.connection.get_table_schema(table_name)

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
        query = f'SELECT COUNT(*) as count FROM {table}'  # noqa: S608
        if where_clause:
            query += f' WHERE {where_clause}'

        result = self.fetch_one(query, parameters)
        return result['count'] if result else 0

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
        query = f'SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1'  # noqa: S608
        result = self.fetch_one(query, parameters)
        return result is not None
