import pathlib


def get_path_without_filename(path: pathlib.Path) -> pathlib.Path:
    """Return path without filename."""
    return path.parent


def get_path_extension(path: pathlib.Path) -> str:
    """Return file extension from path."""
    return path.suffix


def get_path_filename(path: pathlib.Path) -> str:
    """Return filename from path."""
    return path.name


def dir_exists(path: pathlib.Path) -> bool:
    """Check if directory exists."""
    return path.exists() and path.is_dir()


def file_exists(path: pathlib.Path) -> bool:
    """Check if file exists."""
    return path.exists()


def write_file(
    path: pathlib.Path, content: str | bytes, override: bool = False
) -> bool:
    """Write content to file. Return True if file was written, False otherwise."""
    if not override and file_exists(path):
        return False

    path.write_text(content) if isinstance(content, str) else path.write_bytes(content)

    return True


def read_file(path: pathlib.Path, read_bytes: bool = False) -> str | None:
    """Read file contents. Return None if file does not exist or content is empty."""
    if file_exists(path):
        content = path.read_bytes() if read_bytes else path.read_text()
        return content

    return None
