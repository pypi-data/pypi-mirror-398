from amsdal_models.storage.base import Storage

from amsdal.configs.main import settings

_DEFAULT_STORAGE = None


def set_default_storage(storage: Storage) -> None:
    global _DEFAULT_STORAGE  # noqa: PLW0603
    _DEFAULT_STORAGE = storage


def default_storage() -> Storage:
    global _DEFAULT_STORAGE  # noqa: PLW0603

    if _DEFAULT_STORAGE is None:
        # Determine backend from settings
        class_path = settings.DEFAULT_FILE_STORAGE
        _DEFAULT_STORAGE = Storage.from_storage_spec({'storage_class': class_path})
    return _DEFAULT_STORAGE
