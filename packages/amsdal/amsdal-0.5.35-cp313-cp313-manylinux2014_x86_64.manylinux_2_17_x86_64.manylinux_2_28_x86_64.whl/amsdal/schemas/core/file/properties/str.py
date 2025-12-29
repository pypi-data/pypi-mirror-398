def __str__(self) -> str:  # type: ignore[no-untyped-def] # noqa: N807
    return repr(self)


def __repr__(self) -> str:  # type: ignore[no-untyped-def] # noqa: N807
    return f'File<{self.filename}>({self.size or len(self.data) or 0} bytes)'
