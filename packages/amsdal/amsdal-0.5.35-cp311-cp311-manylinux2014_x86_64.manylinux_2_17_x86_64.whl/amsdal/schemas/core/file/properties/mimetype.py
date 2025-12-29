@property  # type: ignore[misc]
def mimetype(self) -> str | None:  # type: ignore[no-untyped-def]
    """
    Returns the MIME type of the file based on its filename.

    This method uses the `mimetypes` module to guess the MIME type of the file.

    Returns:
        str | None: The guessed MIME type of the file, or None if it cannot be determined.
    """
    import mimetypes

    return mimetypes.guess_type(self.filename)[0]
