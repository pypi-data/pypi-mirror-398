import hashlib
import secrets
from typing import Literal

HashAlgorithm = Literal["sha256", "sha3_256", "blake2b"]


def hash_bytes(data: bytes, algorithm: HashAlgorithm = "sha256") -> str:
    """Hash raw bytes and return a hex encoded digest."""
    if algorithm == "sha256":
        return hashlib.sha256(data).hexdigest()
    elif algorithm == "sha3_256":
        return hashlib.sha3_256(data).hexdigest()
    elif algorithm == "blake2b":
        return hashlib.blake2b(data).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def hash_text(text: str, algorithm: HashAlgorithm = "sha256", encoding: str = "utf-8") -> str:
    """Hash text using the given encoding and return a hex encoded digest."""
    return hash_bytes(text.encode(encoding), algorithm=algorithm)


def random_token(length: int = 32) -> str:
    """Generate a cryptographically strong random token as hex string."""
    if length <= 0:
        raise ValueError("length must be positive")
    # Each byte gives two hex characters
    num_bytes = (length + 1) // 2
    token = secrets.token_hex(num_bytes)
    return token[:length]
