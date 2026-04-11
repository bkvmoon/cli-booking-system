"""Shared test fixtures and configuration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

# Ensure local src-layout package imports work with plain `pytest`.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def tmp_json_file(tmp_path: Path) -> Path:
    """Create a temporary JSON file with sample data."""
    data = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
    file_path = tmp_path / "sample.json"
    file_path.write_text(json.dumps(data))
    return file_path


@pytest.fixture
def tmp_csv_file(tmp_path: Path) -> Path:
    """Create a temporary CSV file with sample data."""
    file_path = tmp_path / "sample.csv"
    file_path.write_text("name,age\nAlice,30\nBob,25\n")
    return file_path


@pytest.fixture
def tmp_text_file(tmp_path: Path) -> Path:
    """Create a temporary text file with sample data."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("line one\nline two\nline three\n")
    return file_path
