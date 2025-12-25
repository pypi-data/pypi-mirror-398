import random
import re
import string
from typing import List


SLUG_INVALID = re.compile(r"[^a-z0-9]+")


def slugify(value: str, separator: str = "-") -> str:
    """Convert a string into a lowercase slug."""
    value = value.lower()
    value = SLUG_INVALID.sub(separator, value)
    value = value.strip(separator)
    return value


def to_snake_case(value: str) -> str:
    """Convert a string in camelCase or PascalCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", value)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()


def to_camel_case(value: str) -> str:
    """Convert a string with separators into CamelCase."""
    parts = re.split(r"[_\-\s]+", value)
    return "".join(p.capitalize() for p in parts if p)


def random_string(length: int = 16) -> str:
    """Generate a random ASCII string for testing and temporary IDs."""
    if length <= 0:
        raise ValueError("length must be positive")
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def extract_numbers(value: str) -> List[float]:
    """Extract all numbers (integer and float) from a string."""
    numbers: List[float] = []
    for match in re.finditer(r"[-+]?\d*\.\d+|[-+]?\d+", value):
        numbers.append(float(match.group(0)))
    return numbers


def truncate(value: str, max_length: int, suffix: str = "...") -> str:
    """Truncate a string to a maximum length, adding a suffix if needed."""
    if max_length <= len(suffix):
        raise ValueError("max_length must be greater than length of suffix")
    if len(value) <= max_length:
        return value
    return value[: max_length - len(suffix)] + suffix
