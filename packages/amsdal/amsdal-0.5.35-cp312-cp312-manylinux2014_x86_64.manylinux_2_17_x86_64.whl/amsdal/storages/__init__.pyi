from _typeshed import Incomplete
from amsdal.configs.main import settings as settings
from amsdal_models.storage.base import Storage

_DEFAULT_STORAGE: Incomplete

def set_default_storage(storage: Storage) -> None: ...
def default_storage() -> Storage: ...
