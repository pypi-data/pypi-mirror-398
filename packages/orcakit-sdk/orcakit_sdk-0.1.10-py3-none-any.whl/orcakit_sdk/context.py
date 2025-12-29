"""Context and configuration utilities for OrcaKit SDK."""

from __future__ import annotations

import os
from dataclasses import dataclass, fields
from typing import Any, get_type_hints


@dataclass
class EnvAwareConfig:
    """Base configuration class that supports loading values from environment variables.

    This class automatically loads configuration values from environment variables
    based on field names. Field names are converted to uppercase for environment
    variable lookup.

    Example:
        >>> @dataclass
        ... class MyConfig(EnvAwareConfig):
        ...     host: str = "localhost"
        ...     port: int = 8080
        >>>
        >>> # With HOST=0.0.0.0 and PORT=9000 in environment
        >>> config = MyConfig.from_env()
        >>> config.host  # "0.0.0.0"
        >>> config.port  # 9000
    """

    @classmethod
    def from_env(cls, prefix: str = "") -> EnvAwareConfig:
        """Create a configuration instance from environment variables.

        Args:
            prefix: Optional prefix for environment variable names.

        Returns:
            Configuration instance with values from environment.
        """
        kwargs: dict[str, Any] = {}
        type_hints = get_type_hints(cls)

        for field in fields(cls):
            env_name = f"{prefix}{field.name}".upper()
            env_value = os.environ.get(env_name)

            if env_value is not None:
                field_type = type_hints.get(field.name, str)
                # Handle basic type conversion
                if field_type is bool:
                    kwargs[field.name] = env_value.lower() in ("true", "1", "yes")
                elif field_type is int:
                    kwargs[field.name] = int(env_value)
                elif field_type is float:
                    kwargs[field.name] = float(env_value)
                else:
                    kwargs[field.name] = env_value

        return cls(**kwargs)
