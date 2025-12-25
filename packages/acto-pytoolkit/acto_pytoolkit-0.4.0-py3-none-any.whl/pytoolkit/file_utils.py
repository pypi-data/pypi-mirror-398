import json
import os
import tempfile
from typing import Any

from .crypto_utils import hash_bytes


def read_text(path: str, encoding: str = "utf-8") -> str:
    """Read a text file with the given encoding."""
    with open(path, encoding=encoding) as f:
        return f.read()


def write_text(path: str, content: str, encoding: str = "utf-8") -> None:
    """Write a text file with the given encoding."""
    with open(path, "w", encoding=encoding) as f:
        f.write(content)


def read_json(path: str, encoding: str = "utf-8") -> Any:
    """Read a JSON file and return the parsed data."""
    with open(path, encoding=encoding) as f:
        return json.load(f)


def write_json(path: str, data: Any, encoding: str = "utf-8", indent: int = 2) -> None:
    """Write JSON data to a file."""
    with open(path, "w", encoding=encoding) as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def atomic_write(path: str, data: str, encoding: str = "utf-8") -> None:
    """Atomically write text data to a file.

    This first writes to a temporary file in the same directory and then renames it.
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp_path = tempfile.mkstemp(dir=directory)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as tmp_file:
            tmp_file.write(data)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                # If this fails it is safe to ignore because the target file
                # already exists.
                pass


def file_hash(path: str, algorithm: str = "sha256") -> str:
    """Compute the hash of a file with the given algorithm."""
    h_data = bytearray()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h_data.extend(chunk)
    return hash_bytes(bytes(h_data), algorithm=algorithm)  # type: ignore[arg-type]


def safe_delete(path: str) -> None:
    """Try to delete a file, ignoring missing files."""
    try:
        os.remove(path)
    except FileNotFoundError:
        return
