"""Serialization utilities for JSON, YAML, and TOML."""
from typing import Any
import json

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


def to_json(data: Any, indent: int = 2) -> str:
    """Serialize data to JSON string."""
    return json.dumps(data, indent=indent, ensure_ascii=False)


def from_json(text: str) -> Any:
    """Deserialize JSON string into Python objects."""
    return json.loads(text)


def load_json(filepath: str, encoding: str = "utf-8") -> Any:
    """Load JSON data from a file."""
    with open(filepath, "r", encoding=encoding) as f:
        return json.load(f)


def save_json(filepath: str, data: Any, indent: int = 2, encoding: str = "utf-8") -> None:
    """Save data to a JSON file."""
    with open(filepath, "w", encoding=encoding) as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def to_yaml(data: Any) -> str:
    """Serialize data to YAML string if PyYAML is available."""
    if yaml is None:
        raise RuntimeError("PyYAML is not installed")
    return yaml.safe_dump(data, sort_keys=False)


def from_yaml(text: str) -> Any:
    """Deserialize YAML string into Python objects."""
    if yaml is None:
        raise RuntimeError("PyYAML is not installed")
    return yaml.safe_load(text)


def load_yaml(filepath: str, encoding: str = "utf-8") -> Any:
    """Load YAML data from a file."""
    if yaml is None:
        raise RuntimeError("PyYAML is not installed")
    with open(filepath, "r", encoding=encoding) as f:
        return yaml.safe_load(f)


def save_yaml(filepath: str, data: Any, encoding: str = "utf-8") -> None:
    """Save data to a YAML file."""
    if yaml is None:
        raise RuntimeError("PyYAML is not installed")
    with open(filepath, "w", encoding=encoding) as f:
        yaml.safe_dump(data, f, sort_keys=False)
