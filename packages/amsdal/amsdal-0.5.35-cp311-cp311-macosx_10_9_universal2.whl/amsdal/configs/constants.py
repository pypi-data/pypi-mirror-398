import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

TYPE_SCHEMAS_PATH: Path = BASE_DIR / 'schemas' / 'types'
CORE_SCHEMAS_PATH: Path = BASE_DIR / 'schemas' / 'core'

CORE_MIGRATIONS_PATH: Path = BASE_DIR / '__migrations__'

# Environment
TESTING_ENVIRONMENT = 'testing'
DEVELOPMENT_ENVIRONMENT = 'development'
PRODUCTION_ENVIRONMENT = 'production'


def get_default_environment() -> str:
    """
    Determines the default environment based on the command used to run the script.

    This function checks the command used to run the script and returns the appropriate
    environment string. If the script is run using `pytest`, it returns 'testing'. Otherwise,
    it returns 'development'.

    Returns:
        str: The default environment string, either 'testing' or 'development'.
    """
    cmd = sys.argv[0] if sys.argv else ''

    if 'pytest' in cmd:
        return TESTING_ENVIRONMENT

    return DEVELOPMENT_ENVIRONMENT
