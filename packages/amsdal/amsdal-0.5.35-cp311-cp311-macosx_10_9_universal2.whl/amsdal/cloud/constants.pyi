from _typeshed import Incomplete
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config: Incomplete
    AMSDAL_SANDBOX_ENVIRONMENT: bool | None

JWT_PUBLIC_KEY: str
ENCRYPT_PUBLIC_KEY: str
cloud_settings: Incomplete
SYNC_KEY: bytes
AMSDAL_ENV_SUBDOMAIN: Incomplete
BASE_AUTH_URL: Incomplete
