from _typeshed import Incomplete
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Settings configuration for the application.

    This class uses Pydantic's BaseSettings to manage application settings
    from environment variables and a .env file.

    Attributes:
        model_config (SettingsConfigDict): Configuration for Pydantic settings.
        ADMIN_USER_EMAIL (str | None): The email of the admin user.
        ADMIN_USER_PASSWORD (str | None): The password of the admin user.
        AUTH_JWT_KEY (str | None): The key used for JWT authentication.
        AUTH_TOKEN_EXPIRATION (int): The expiration time for authentication tokens in seconds.
        REQUIRE_DEFAULT_AUTHORIZATION (bool): Flag to require default authorization.
        REQUIRE_MFA_BY_DEFAULT (bool): Flag to require MFA for all users by default.
        MFA_TOTP_ISSUER (str): The issuer name displayed in TOTP authenticator apps.
        MFA_BACKUP_CODES_COUNT (int): Number of backup codes to generate per user.
        MFA_EMAIL_CODE_EXPIRATION (int): Email MFA code expiration time in seconds.
    """
    model_config: Incomplete
    ADMIN_USER_EMAIL: str | None
    ADMIN_USER_PASSWORD: str | None
    AUTH_JWT_KEY: str | None
    AUTH_TOKEN_EXPIRATION: int
    REQUIRE_DEFAULT_AUTHORIZATION: bool
    REQUIRE_MFA_BY_DEFAULT: bool
    MFA_TOTP_ISSUER: str
    MFA_BACKUP_CODES_COUNT: int
    MFA_EMAIL_CODE_EXPIRATION: int

auth_settings: Incomplete
