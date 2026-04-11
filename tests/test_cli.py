"""Unit tests for the CLI interface using Click's test runner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

import gic_cinema_booking.cli as cli_module
from gic_cinema_booking.cli import app


class TestCLIVersion:
    """Tests for the version option."""

    def test_version_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "GIC" in result.output

    def test_interactive_menu_blank_then_success(self, runner: CliRunner) -> None:
        result = runner.invoke(app, input="\nInception 2 2\n3\n")
        assert result.exit_code == 0
        assert "Please define movie title and seating map" in result.output

    def test_interactive_invalid_three_values_then_success(
        self, runner: CliRunner
    ) -> None:
        result = runner.invoke(app, input="only_two\nInception 2 2\n3\n")
        assert result.exit_code == 0
        assert "exactly 3 values" in result.output

    def test_interactive_rows_over_limit_then_success(self, runner: CliRunner) -> None:
        result = runner.invoke(app, input="M 27 5\nInception 2 2\n3\n")
        assert result.exit_code == 0
        assert "Maximum rows allowed 26" in result.output

    def test_interactive_seats_per_row_over_limit_then_success(
        self, runner: CliRunner
    ) -> None:
        result = runner.invoke(app, input="M 5 51\nInception 2 2\n3\n")
        assert result.exit_code == 0
        assert "Maximum seats per row allowed 50" in result.output

    def test_interactive_invalid_numeric_layout_then_success(
        self, runner: CliRunner
    ) -> None:
        result = runner.invoke(app, input="M x y\nInception 2 2\n3\n")
        assert result.exit_code == 0
        assert "Error:" in result.output

    def test_interactive_exit_from_main_menu(self, runner: CliRunner) -> None:
        result = runner.invoke(app, input="Inception 2 2\n3\n")
        assert result.exit_code == 0
        assert "Welcome to GIC Cinemas" in result.output
        assert "Bye!" in result.output

    def test_interactive_invalid_menu_choice_then_exit(self, runner: CliRunner) -> None:
        result = runner.invoke(app, input="Inception 2 2\n9\n3\n")
        assert result.exit_code == 0
        assert "Invalid choice" in result.output

    def test_interactive_blank_menu_choice_ignored_then_exit(
        self, runner: CliRunner
    ) -> None:
        result = runner.invoke(app, input="Inception 2 2\n\n3\n")
        assert result.exit_code == 0

    def test_interactive_book_one_ticket_accept_default_then_exit(
        self, runner: CliRunner
    ) -> None:
        # seat map -> menu book -> 1 ticket -> blank accept seat -> main menu exit
        result = runner.invoke(app, input="Inception 2 5\n1\n1\n\n3\n")
        assert result.exit_code == 0
        assert "Successfully reserved" in result.output
        assert "GIC0001" in result.output

    def test_interactive_book_invalid_ticket_count_then_success(
        self, runner: CliRunner
    ) -> None:
        result = runner.invoke(app, input="Inception 2 2\n1\nxx\n1\n\n3\n")
        assert result.exit_code == 0
        assert "valid number" in result.output

    def test_interactive_book_too_many_tickets_then_success(
        self, runner: CliRunner
    ) -> None:
        result = runner.invoke(app, input="Inception 2 2\n1\n99\n1\n\n3\n")
        assert result.exit_code == 0
        assert "Only" in result.output and "available" in result.output

    def test_interactive_check_booking_flow(self, runner: CliRunner) -> None:
        result = runner.invoke(app, input="Inception 2 2\n1\n1\n\n2\nGIC0001\n3\n")
        assert result.exit_code == 0
        assert "Booking id:" in result.output

    def test_interactive_check_invalid_id_then_exit(self, runner: CliRunner) -> None:
        result = runner.invoke(app, input="Inception 2 2\n2\nNOPE\n\n3\n")
        assert result.exit_code == 0
        assert "Invalid booking id" in result.output

    def test_interactive_book_blank_ticket_prompt_then_confirm(
        self, runner: CliRunner
    ) -> None:
        # Blank on ticket prompt returns to menu, then book 1 ticket and accept seat
        result = runner.invoke(app, input="Inception 2 2\n1\n\n1\n1\n\n3\n")
        assert result.exit_code == 0
        assert "GIC0001" in result.output

    def test_interactive_book_ticket_value_error(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def boom(self: object, tickets: int) -> None:
            raise ValueError("allocation failed")

        monkeypatch.setattr(cli_module.BookingManager, "book_ticket", boom)
        result = runner.invoke(app, input="Inception 2 2\n1\n1\n\n3\n")
        assert result.exit_code == 0
        assert "allocation failed" in result.output

    def test_interactive_check_booking_value_error(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def boom(self: object) -> list[list[str]]:
            raise ValueError("map failed")

        monkeypatch.setattr(cli_module.BookingManager, "get_copy_all_bookings", boom)
        # After the error the check loop continues; blank returns to main menu, then exit.
        result = runner.invoke(app, input="Inception 2 2\n1\n1\n\n2\nGIC0001\n\n3\n")
        assert result.exit_code == 0
        assert "map failed" in result.output


class TestHelloCommand:
    """Tests for the hello command - REMOVED from CLI."""

    @pytest.mark.skip(reason="hello command removed from CLI")
    def test_basic_hello(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["hello", "World"])
        assert result.exit_code == 0
        assert "Hello, World!" in result.output

    @pytest.mark.skip(reason="hello command removed from CLI")
    def test_custom_greeting(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["hello", "World", "--greeting", "Hi"])
        assert result.exit_code == 0
        assert "Hi, World!" in result.output

    @pytest.mark.skip(reason="hello command removed from CLI")
    def test_uppercase_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["hello", "World", "--uppercase"])
        assert result.exit_code == 0
        assert "HELLO, WORLD!" in result.output

    @pytest.mark.skip(reason="hello command removed from CLI")
    def test_count_option(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["hello", "World", "--count", "2"])
        assert result.exit_code == 0
        assert result.output.count("Hello, World!") == 2

    @pytest.mark.skip(reason="hello command removed from CLI")
    def test_empty_name_error(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["hello", ""])
        assert result.exit_code == 1
        assert "Error" in result.output

    @pytest.mark.skip(reason="hello command removed from CLI")
    def test_missing_name_argument(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["hello"])
        assert result.exit_code != 0

    @pytest.mark.skip(reason="hello command removed from CLI")
    def test_hello_help(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["hello", "--help"])
        assert result.exit_code == 0
        assert "NAME" in result.output


class TestProcessCommand:
    """Tests for the process command - REMOVED from CLI."""

    @pytest.mark.skip(reason="process command removed from CLI")
    def test_process_text_file(self, runner: CliRunner, tmp_text_file) -> None:
        result = runner.invoke(app, ["process", str(tmp_text_file)])
        assert result.exit_code == 0
        assert "Processed 3 rows" in result.output

    @pytest.mark.skip(reason="process command removed from CLI")
    def test_process_json_file(self, runner: CliRunner, tmp_json_file) -> None:
        result = runner.invoke(app, ["process", str(tmp_json_file)])
        assert result.exit_code == 0
        assert "Processed 2 rows" in result.output

    @pytest.mark.skip(reason="process command removed from CLI")
    def test_process_with_output(
        self, runner: CliRunner, tmp_text_file, tmp_path
    ) -> None:
        output = tmp_path / "out.txt"
        result = runner.invoke(
            app, ["process", str(tmp_text_file), "--output", str(output)]
        )
        assert result.exit_code == 0

    @pytest.mark.skip(reason="process command removed from CLI")
    def test_process_missing_file(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["process", "/nonexistent/file.txt"])
        assert result.exit_code != 0

    @pytest.mark.skip(reason="process command removed from CLI")
    def test_process_invalid_format(self, runner: CliRunner, tmp_text_file) -> None:
        result = runner.invoke(app, ["process", str(tmp_text_file), "--format", "xml"])
        assert result.exit_code != 0

    @pytest.mark.skip(reason="process command removed from CLI")
    def test_process_help(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["process", "--help"])
        assert result.exit_code == 0
        assert "INPUT_FILE" in result.output

    @pytest.mark.skip(reason="process command removed from CLI")
    def test_process_file_not_found_in_handler(
        self, runner: CliRunner, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "exists.txt"
        path.write_text("x")

        def boom(**_kwargs: object) -> dict[str, object]:
            raise FileNotFoundError("missing")

        monkeypatch.setattr(cli_module, "process_data", boom)
        result = runner.invoke(app, ["process", str(path)])
        assert result.exit_code == 1
        assert "Error:" in result.output

    @pytest.mark.skip(reason="process command removed from CLI")
    def test_process_value_error_in_handler(
        self, runner: CliRunner, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "exists.txt"
        path.write_text("x")

        def boom(**_kwargs: object) -> dict[str, object]:
            raise ValueError("bad format")

        monkeypatch.setattr(cli_module, "process_data", boom)
        result = runner.invoke(app, ["process", str(path)])
        assert result.exit_code == 1
        assert "Invalid format" in result.output


class TestCLIFallbackConsole:
    """Exercise Rich-import fallback in a clean interpreter (no sys.modules pollution)."""

    def test_console_fallback_subprocess(self) -> None:
        """Test fallback in a clean subprocess without rich."""
        root = Path(__file__).resolve().parents[1]
        src = root / "src"
        script = f"""
import builtins
import sys
sys.path.insert(0, {str(src)!r})
_real_import = builtins.__import__

def _import(name, globals_arg=None, locals_arg=None, fromlist=(), level=0):
    if name == "rich.console" or name.startswith("rich."):
        raise ModuleNotFoundError(name)
    return _real_import(name, globals_arg, locals_arg, fromlist, level)

builtins.__import__ = _import
import gic_cinema_booking.cli as cli
import gic_cinema_booking.services as svc
cli.Console().print("cli_ok")
svc.Console().print("svc_ok")
"""
        proc = subprocess.run(
            [sys.executable, "-c", script],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert "cli_ok" in proc.stdout
        assert "svc_ok" in proc.stdout
