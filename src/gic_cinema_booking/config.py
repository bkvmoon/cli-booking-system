"""Configuration module for the GIC Cinemas booking system.

This module provides a dataclass-based configuration system that loads
application settings from environment variables. It supports settings for
application name, debug mode, logging level, data directory, and retry limits.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    """Immutable configuration class for application settings.

    This dataclass holds all configuration values for the application.
    It is frozen to ensure configuration values cannot be modified after
    initialization, providing thread safety and preventing accidental
    configuration changes during runtime.

    Attributes:
        app_name: The name of the application (default: "CLI Best Practices").
        debug: Whether debug mode is enabled (default: False).
        log_level: The logging level to use (default: "INFO").
        data_dir: The directory path for data storage (default: cwd/data).
        max_retries: Maximum number of retry attempts (default: 3).
    """

    app_name: str = "CLI Best Practices"
    debug: bool = False
    log_level: str = "INFO"
    data_dir: Path = field(default_factory=lambda: Path.cwd() / "data")
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> Config:
        """Create a Config instance populated from environment variables.

        This class method reads configuration values from the environment
        and returns a new Config instance. If an environment variable is not
        set, the default value is used instead.

        Environment Variables:
            CLI_APP_NAME: The application name (default: "CLI Best Practices").
            CLI_DEBUG: Debug mode flag ("true", "1", "yes" enable debug mode).
            CLI_LOG_LEVEL: Logging level (default: "INFO").
            CLI_DATA_DIR: Path to the data directory (default: cwd/data).
            CLI_MAX_RETRIES: Maximum retry attempts (default: 3).

        Returns:
            A Config instance with values loaded from the environment.
        """
        return cls(
            app_name=os.getenv("CLI_APP_NAME", cls.app_name),
            debug=os.getenv("CLI_DEBUG", "false").lower() in ("true", "1", "yes"),
            log_level=os.getenv("CLI_LOG_LEVEL", "INFO").upper(),
            data_dir=Path(os.getenv("CLI_DATA_DIR", str(Path.cwd() / "data"))),
            max_retries=int(os.getenv("CLI_MAX_RETRIES", "3")),
        )
