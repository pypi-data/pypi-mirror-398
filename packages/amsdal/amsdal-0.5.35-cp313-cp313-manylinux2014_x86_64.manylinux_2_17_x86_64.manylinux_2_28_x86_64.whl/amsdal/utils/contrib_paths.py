from collections.abc import Generator
from importlib import import_module
from pathlib import Path


def get_contrib_schemas_paths() -> Generator[Path, None, None]:
    """
    Retrieves paths to contribution schemas.

    This function iterates over the configured contributions in the settings and yields
    the paths to the 'models' directories for each contribution.

    Returns:
        Generator[Path, None, None]: A generator that yields paths to the 'models' directories
        of the configured contributions.
    """
    from amsdal.configs.main import settings

    for contrib in settings.CONTRIB:
        module_name, *_ = contrib.rsplit('.', 2)
        module = import_module(module_name)

        yield Path(module.__file__).parent / 'models'  # type: ignore[arg-type]
