from enum import Enum

class AuthType(Enum):
    """
    Enumeration for authentication types.

    This enum defines the types of authentication methods available.

    Attributes:
        CREDENTIALS: Authentication using credentials.
        TOKEN: Authentication using a token.
    """
    CREDENTIALS = ...
    TOKEN = ...

class DeployType(str, Enum):
    """
    Enumeration for deployment types.

    This enum defines the types of deployment methods available.

    Attributes:
        lakehouse_only: Deployment only to the lakehouse.
        include_state_db: Deployment including the state database.
    """
    lakehouse_only = 'lakehouse_only'
    include_state_db = 'include_state_db'

class StateOption(str, Enum):
    """
    Enumeration for state options.

    This enum defines the types of state database options available.

    Attributes:
        sqlite: State database using SQLite.
        postgres: State database using PostgreSQL.
    """
    sqlite = 'sqlite'
    postgres = 'postgres'

class LakehouseOption(str, Enum):
    """
    Enumeration for lakehouse options.

    This enum defines the types of lakehouse options available.

    Attributes:
        spark: Lakehouse option using Spark.
        postgres: Lakehouse option using PostgreSQL.
        postgres_immutable: Lakehouse option using immutable PostgreSQL.
    """
    spark = 'spark'
    postgres = 'postgres'
    postgres_immutable = 'postgres-immutable'

class ResponseStatus(str, Enum):
    """
    Enumeration for response statuses.

    This enum defines the types of response statuses available.

    Attributes:
        success: Indicates a successful response.
        error: Indicates an error response.
    """
    success = 'success'
    error = 'error'
