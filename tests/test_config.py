"""Unit tests for the configuration module."""

from __future__ import annotations

from pathlib import Path

from gic_cinema_booking.config import Config


class TestConfig:
    """Tests for the Config dataclass."""

    def test_default_config(self) -> None:
        config = Config()
        assert config.app_name == "CLI Best Practices"
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.max_retries == 3

    def test_from_env_defaults(self) -> None:
        config = Config.from_env()
        assert config.app_name == "CLI Best Practices"
        assert config.debug is False

    def test_from_env_custom(self, monkeypatch) -> None:
        monkeypatch.setenv("CLI_APP_NAME", "My App")
        monkeypatch.setenv("CLI_DEBUG", "true")
        monkeypatch.setenv("CLI_LOG_LEVEL", "debug")
        monkeypatch.setenv("CLI_MAX_RETRIES", "5")

        config = Config.from_env()
        assert config.app_name == "My App"
        assert config.debug is True
        assert config.log_level == "DEBUG"
        assert config.max_retries == 5

    def test_from_env_debug_variants(self, monkeypatch) -> None:
        for truthy_val in ["true", "1", "yes"]:
            monkeypatch.setenv("CLI_DEBUG", truthy_val)
            assert Config.from_env().debug is True

        for falsy_val in ["false", "0", "no", ""]:
            monkeypatch.setenv("CLI_DEBUG", falsy_val)
            assert Config.from_env().debug is False

    def test_config_is_frozen(self) -> None:
        config = Config()
        import pytest

        with pytest.raises(AttributeError):
            config.debug = True  # type: ignore[misc]

    def test_data_dir_from_env(self, monkeypatch, tmp_path: Path) -> None:
        monkeypatch.setenv("CLI_DATA_DIR", str(tmp_path))
        config = Config.from_env()
        assert config.data_dir == tmp_path
