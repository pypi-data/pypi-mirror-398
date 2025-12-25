import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from dotenv import load_dotenv

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore

try:
    import tomli  # type: ignore
except ImportError:  # pragma: no cover
    tomli = None  # type: ignore


@dataclass
class ConfigLoader:
    """Configuration loader that can merge multiple sources.

    Priority order (later overwrites earlier):
    1. Values from JSON file
    2. Values from YAML file
    3. Values from TOML file
    4. Values from environment variables
    """

    env_file: Optional[str] = None
    json_file: Optional[str] = None
    yaml_file: Optional[str] = None
    toml_file: Optional[str] = None
    prefix: Optional[str] = None
    _data: Dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.env_file:
            # Load variables from .env file into the environment
            load_dotenv(self.env_file)

        # Load from JSON
        if self.json_file and os.path.exists(self.json_file):
            with open(self.json_file, "r", encoding="utf-8") as f:
                content = json.load(f)
            self._merge_dict(content)

        # Load from YAML
        if self.yaml_file and os.path.exists(self.yaml_file):
            if yaml is None:
                raise RuntimeError("PyYAML is not installed but yaml_file is specified.")
            with open(self.yaml_file, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
            if isinstance(content, dict):
                self._merge_dict(content)

        # Load from TOML
        if self.toml_file and os.path.exists(self.toml_file):
            if tomllib:
                with open(self.toml_file, "rb") as f:
                    content = tomllib.load(f)
            elif tomli:
                with open(self.toml_file, "rb") as f:
                    content = tomli.load(f)
            else:
                raise RuntimeError("No TOML parser available but toml_file is specified.")
            if isinstance(content, dict):
                self._merge_dict(content)

        # Environment variables override everything
        env_prefix = (self.prefix or "").upper()
        for key, value in os.environ.items():
            if env_prefix:
                if key.startswith(env_prefix):
                    clean_key = key[len(env_prefix) :].lstrip("_")
                    self._data[clean_key] = value
            else:
                self._data[key] = value

    def _merge_dict(self, other: Dict[str, Any]) -> None:
        """Merge a dictionary into the internal config dictionary.

        Nested dictionaries are flattened using dots.
        """

        def flatten(prefix: str, value: Any) -> None:
            if isinstance(value, dict):
                for k, v in value.items():
                    new_prefix = f"{prefix}.{k}" if prefix else k
                    flatten(new_prefix, v)
            else:
                self._data[prefix] = value

        flatten("", other)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Retrieve a configuration value with an optional default."""
        return self._data.get(key, default)

    def require(self, key: str) -> Any:
        """Retrieve a configuration value or raise a KeyError if it is missing."""
        if key not in self._data:
            raise KeyError(f"Missing configuration key: {key}")
        return self._data[key]

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """Retrieve a configuration value and cast it to int if present."""
        value = self.get(key, default)
        if value is None:
            return None
        return int(value)

    def get_float(self, key: str, default: Optional[float] = None) -> Optional[float]:
        """Retrieve a configuration value and cast it to float if present."""
        value = self.get(key, default)
        if value is None:
            return None
        return float(value)

    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """Retrieve a configuration value and interpret it as boolean.

        Recognized truthy values: "1", "true", "yes", "on" (case insensitive).
        Recognized falsy values: "0", "false", "no", "off" (case insensitive).
        """
        value = self.get(key, default)
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
        # Fallback: not recognized, return default
        return default

    def as_dict(self) -> Dict[str, Any]:
        """Return a copy of the configuration data as a dictionary."""
        return dict(self._data)
