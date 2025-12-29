from pathlib import Path
from typing import BinaryIO


def to_file(self, file_or_path: Path | BinaryIO) -> None:  # type: ignore[no-untyped-def]
    """
    Writes the object's data to a file path or a binary file object.

    Args:
        file_or_path (Path | BinaryIO): The file path or binary file object where the data will be written.

    Returns:
        None

    Raises:
        ValueError: If the provided path is a directory.
    """
    if isinstance(file_or_path, Path):
        if file_or_path.is_dir():
            file_or_path = file_or_path / self.name
        file_or_path.write_bytes(self.data)  # type: ignore[union-attr]
    else:
        file_or_path.write(self.data)
        file_or_path.seek(0)
