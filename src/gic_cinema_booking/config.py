"""Application configuration with environment variable support."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from environment variables."""

    app_name: str = "CLI Best Practices"
    debug: bool = False
    log_level: str = "INFO"
    data_dir: Path = field(default_factory=lambda: Path.cwd() / "data")
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> Config:
        """Create configuration from environment variables.

        Returns:
            Config instance with values from environment.
        """
        return cls(
            app_name=os.getenv("CLI_APP_NAME", cls.app_name),
            debug=os.getenv("CLI_DEBUG", "false").lower() in ("true", "1", "yes"),
            log_level=os.getenv("CLI_LOG_LEVEL", "INFO").upper(),
            data_dir=Path(os.getenv("CLI_DATA_DIR", str(Path.cwd() / "data"))),
            max_retries=int(os.getenv("CLI_MAX_RETRIES", "3")),
        )
