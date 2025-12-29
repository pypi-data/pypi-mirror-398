import base64
from contextlib import suppress

from pydantic import field_validator


@field_validator('data')  # type: ignore[misc]
@classmethod
def data_base64_decode(cls, v: bytes) -> bytes:  # type: ignore[no-untyped-def]
    """
    Decodes a base64-encoded byte string if it is base64-encoded.

    This method checks if the provided byte string is base64-encoded and decodes it if true.
    If the byte string is not base64-encoded, it returns the original byte string.

    Args:
        cls: The class this method belongs to.
        v (bytes): The byte string to be checked and potentially decoded.

    Returns:
        bytes: The decoded byte string if it was base64-encoded, otherwise the original byte string.
    """
    is_base64: bool = False

    with suppress(Exception):
        is_base64 = base64.b64encode(base64.b64decode(v)) == v

    if is_base64:
        return base64.b64decode(v)

    return v
