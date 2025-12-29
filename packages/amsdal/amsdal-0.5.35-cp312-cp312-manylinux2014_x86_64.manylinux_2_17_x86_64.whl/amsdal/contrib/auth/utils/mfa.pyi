from amsdal.contrib.auth.models.mfa_device import MFADevice as MFADevice
from amsdal.contrib.auth.models.user import User as User
from amsdal.contrib.auth.settings import auth_settings as auth_settings
from datetime import datetime
from enum import StrEnum

class DeviceType(StrEnum):
    TOTP = 'totp'
    BACKUP_CODE = 'backup_code'
    EMAIL = 'email'
    SMS = 'sms'

def get_active_user_devices(user: User) -> dict[DeviceType, list['MFADevice']]: ...
async def aget_active_user_devices(user: User) -> dict[DeviceType, list['MFADevice']]: ...
def generate_totp_secret() -> str:
    """
    Generate a new TOTP secret key.

    Returns:
        str: A base32-encoded random secret key.
    """
def generate_qr_code_url(secret: str, email: str, issuer: str | None = None) -> str:
    """
    Generate a QR code URL for TOTP device setup.

    This creates an otpauth:// URL that can be scanned by authenticator apps
    like Google Authenticator, Authy, etc.

    Args:
        secret (str): The TOTP secret key.
        email (str): The user's email address.
        issuer (str | None): The issuer name to display in the app. If None, uses the
            MFA_TOTP_ISSUER setting.

    Returns:
        str: The otpauth:// URL for QR code generation.
    """
def verify_totp_code(secret: str, code: str, digits: int = 6, step: int = 30, valid_window: int = 1) -> bool:
    """
    Verify a TOTP code against a secret.

    This function validates the provided code against the TOTP secret, allowing
    for a time window to account for clock drift between the server and the device.

    Args:
        secret (str): The TOTP secret key.
        code (str): The code to verify.
        digits (int): Number of digits in the code (default: 6).
        step (int): Time step in seconds (default: 30).
        valid_window (int): Number of time steps to check before and after the current time
            (default: 1, which means ±30 seconds with default step).

    Returns:
        bool: True if the code is valid, False otherwise.
    """
def generate_backup_codes(count: int | None = None) -> list[str]:
    """
    Generate a set of backup recovery codes.

    Each code is a random alphanumeric string that can be used once for authentication
    when the primary MFA device is unavailable.

    Args:
        count (int | None): Number of codes to generate. If None, uses the
            MFA_BACKUP_CODES_COUNT setting.

    Returns:
        list[str]: List of generated backup codes.
    """
def hash_backup_code(code: str) -> bytes:
    """
    Hash a backup code for secure storage.

    Uses bcrypt for hashing, similar to password hashing.

    Args:
        code (str): The backup code to hash.

    Returns:
        bytes: The hashed code.
    """
def verify_backup_code(hashed_code: bytes, code: str) -> bool:
    """
    Verify a backup code against its hash.

    Args:
        hashed_code (bytes): The stored hashed code.
        code (str): The code to verify.

    Returns:
        bool: True if the code matches, False otherwise.
    """
def generate_email_mfa_code(length: int = 6) -> str:
    """
    Generate a random numeric code for email-based MFA.

    Args:
        length (int): Length of the code (default: 6).

    Returns:
        str: A random numeric code.
    """
def get_email_code_expiration() -> datetime:
    """
    Calculate the expiration time for an email MFA code.

    Returns:
        datetime: The expiration timestamp.
    """
def is_email_code_valid(code_expires_at: datetime) -> bool:
    """
    Check if an email MFA code is still valid (not expired).

    Args:
        code_expires_at (datetime): The expiration timestamp of the code.

    Returns:
        bool: True if the code is still valid, False if expired.
    """
