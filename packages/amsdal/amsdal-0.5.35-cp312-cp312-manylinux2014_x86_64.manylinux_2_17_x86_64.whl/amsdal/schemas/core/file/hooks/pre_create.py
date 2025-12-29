def pre_create(self) -> None:  # type: ignore[no-untyped-def]
    """
    Prepares the object for creation by setting its size attribute.

    This method calculates the size of the object's data and assigns it to the size attribute.
    If the data is None, it defaults to an empty byte string.

    Args:
        None
    """
    self.size = len(self.data or b'')


async def apre_create(self) -> None:  # type: ignore[no-untyped-def]
    """
    Prepares the object for creation by setting its size attribute.

    This method calculates the size of the object's data and assigns it to the size attribute.
    If the data is None, it defaults to an empty byte string.

    Args:
        None
    """
    self.size = len(self.data or b'')
