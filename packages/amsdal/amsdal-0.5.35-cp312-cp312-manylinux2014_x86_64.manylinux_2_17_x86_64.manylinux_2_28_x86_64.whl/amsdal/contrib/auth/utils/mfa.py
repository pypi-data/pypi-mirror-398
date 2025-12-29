"""
Utilities for Multi-Factor Authentication (MFA).

This module provides helper functions for generating and verifying MFA codes
for different authentication methods (TOTP, backup codes, email codes).
"""

import secrets
import string
import typing as t
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from enum import StrEnum

import pyotp
from amsdal_utils.models.enums import Versions

from amsdal.contrib.auth.settings import auth_settings

if t.TYPE_CHECKING:
    from amsdal.contrib.auth.models.mfa_device import MFADevice
    from amsdal.contrib.auth.models.user import User


class DeviceType(StrEnum):
    TOTP = 'totp'
    BACKUP_CODE = 'backup_code'
    EMAIL = 'email'
    SMS = 'sms'


def get_active_user_devices(user: 'User') -> dict[DeviceType, list['MFADevice']]:
    from amsdal.contrib.auth.models.backup_code import BackupCode
    from amsdal.contrib.auth.models.email_mfa_device import EmailMFADevice
    from amsdal.contrib.auth.models.sms_device import SMSDevice
    from amsdal.contrib.auth.models.totp_device import TOTPDevice

    _result: dict[DeviceType, list[MFADevice]] = {}
    for device_class, device_type in [
        (TOTPDevice, DeviceType.TOTP),
        (BackupCode, DeviceType.BACKUP_CODE),
        (EmailMFADevice, DeviceType.EMAIL),
        (SMSDevice, DeviceType.SMS),
    ]:
        devices = device_class.objects.filter(  # type: ignore[attr-defined]
            user_email=user.email,
            is_active=True,
            confirmed=True,
            _address__object_version=Versions.LATEST,
        ).execute()
        _result[device_type] = devices

    return _result


async def aget_active_user_devices(user: 'User') -> dict[DeviceType, list['MFADevice']]:
    from amsdal.contrib.auth.models.backup_code import BackupCode
    from amsdal.contrib.auth.models.email_mfa_device import EmailMFADevice
    from amsdal.contrib.auth.models.sms_device import SMSDevice
    from amsdal.contrib.auth.models.totp_device import TOTPDevice

    _result: dict[DeviceType, list[MFADevice]] = {}
    for device_class, device_type in [
        (TOTPDevice, DeviceType.TOTP),
        (BackupCode, DeviceType.BACKUP_CODE),
        (EmailMFADevice, DeviceType.EMAIL),
        (SMSDevice, DeviceType.SMS),
    ]:
        devices = await device_class.objects.filter(  # type: ignore[attr-defined]
            user_email=user.email,
            is_active=True,
            confirmed=True,
            _address__object_version=Versions.LATEST,
        ).aexecute()
        _result[device_type] = devices

    return _result


def generate_totp_secret() -> str:
    """
    Generate a new TOTP secret key.

    Returns:
        str: A base32-encoded random secret key.
    """
    return pyotp.random_base32()


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
    if issuer is None:
        issuer = auth_settings.MFA_TOTP_ISSUER

    # Create TOTP object
    totp = pyotp.TOTP(secret)

    # Generate provisioning URI
    uri = totp.provisioning_uri(
        name=email,
        issuer_name=issuer,
    )

    return uri


def verify_totp_code(
    secret: str,
    code: str,
    digits: int = 6,
    step: int = 30,
    valid_window: int = 1,
) -> bool:
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
    try:
        totp = pyotp.TOTP(secret, digits=digits, interval=step)
        return totp.verify(code, valid_window=valid_window)
    except Exception:
        return False


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
    if count is None:
        count = auth_settings.MFA_BACKUP_CODES_COUNT

    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric code (without ambiguous characters)
        alphabet = string.ascii_uppercase + string.digits
        alphabet = alphabet.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
        code = ''.join(secrets.choice(alphabet) for _ in range(8))
        # Format as XXXX-XXXX for readability
        formatted_code = f'{code[:4]}-{code[4:]}'
        codes.append(formatted_code)

    return codes


def hash_backup_code(code: str) -> bytes:
    """
    Hash a backup code for secure storage.

    Uses bcrypt for hashing, similar to password hashing.

    Args:
        code (str): The backup code to hash.

    Returns:
        bytes: The hashed code.
    """
    import bcrypt

    # Remove formatting (dashes) before hashing
    clean_code = code.replace('-', '')
    return bcrypt.hashpw(clean_code.encode('utf-8'), bcrypt.gensalt())


def verify_backup_code(hashed_code: bytes, code: str) -> bool:
    """
    Verify a backup code against its hash.

    Args:
        hashed_code (bytes): The stored hashed code.
        code (str): The code to verify.

    Returns:
        bool: True if the code matches, False otherwise.
    """
    import bcrypt

    try:
        # Remove formatting (dashes) before verification
        clean_code = code.replace('-', '')
        return bcrypt.checkpw(clean_code.encode('utf-8'), hashed_code)
    except Exception:
        return False


def generate_email_mfa_code(length: int = 6) -> str:
    """
    Generate a random numeric code for email-based MFA.

    Args:
        length (int): Length of the code (default: 6).

    Returns:
        str: A random numeric code.
    """
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def get_email_code_expiration() -> datetime:
    """
    Calculate the expiration time for an email MFA code.

    Returns:
        datetime: The expiration timestamp.
    """
    expiration_seconds = auth_settings.MFA_EMAIL_CODE_EXPIRATION
    return datetime.now(tz=UTC) + timedelta(seconds=expiration_seconds)


def is_email_code_valid(code_expires_at: datetime) -> bool:
    """
    Check if an email MFA code is still valid (not expired).

    Args:
        code_expires_at (datetime): The expiration timestamp of the code.

    Returns:
        bool: True if the code is still valid, False if expired.
    """
    return datetime.now(tz=UTC) < code_expires_at
