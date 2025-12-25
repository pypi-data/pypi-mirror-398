import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Environment:
    """Represents the current application environment.

    The environment name is taken from the APP_ENV variable by default.
    Typical values are: "development", "staging", "production".
    """

    name: str = "development"

    @property
    def is_development(self) -> bool:
        return self.name.lower() in {"dev", "development"}

    @property
    def is_staging(self) -> bool:
        return self.name.lower() in {"stage", "staging"}

    @property
    def is_production(self) -> bool:
        return self.name.lower() in {"prod", "production"}


def get_environment(
    var_name: str = "APP_ENV", default: Optional[str] = "development"
) -> Environment:
    """Create an Environment instance from an environment variable."""
    name = os.getenv(var_name, default or "development")
    return Environment(name=name)
