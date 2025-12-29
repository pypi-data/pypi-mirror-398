from _typeshed import Incomplete
from pathlib import Path

BASE_DIR: Incomplete
TYPE_SCHEMAS_PATH: Path
CORE_SCHEMAS_PATH: Path
CORE_MIGRATIONS_PATH: Path
TESTING_ENVIRONMENT: str
DEVELOPMENT_ENVIRONMENT: str
PRODUCTION_ENVIRONMENT: str

def get_default_environment() -> str:
    """
    Determines the default environment based on the command used to run the script.

    This function checks the command used to run the script and returns the appropriate
    environment string. If the script is run using `pytest`, it returns 'testing'. Otherwise,
    it returns 'development'.

    Returns:
        str: The default environment string, either 'testing' or 'development'.
    """
