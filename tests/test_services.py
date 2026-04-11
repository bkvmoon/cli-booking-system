"""Unit tests for the services module."""

from __future__ import annotations

import json
from pathlib import Path

import click
import pytest

from gic_cinema_booking.services import (
    BookingManager,
    _read_rows,
    _write_output,
    greet,
    process_data,
)


class TestGreet:
    """Tests for the greet function."""

    def test_basic_greeting(self) -> None:
        result = greet(name="World")
        assert result == "Hello, World!"

    def test_custom_greeting(self) -> None:
        result = greet(name="World", greeting="Hi")
        assert result == "Hi, World!"

    def test_uppercase_greeting(self) -> None:
        result = greet(name="World", uppercase=True)
        assert result == "HELLO, WORLD!"

    def test_count_greeting(self) -> None:
        result = greet(name="World", count=3)
        assert result == "Hello, World!\nHello, World!\nHello, World!"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="Name cannot be empty"):
            greet(name="")

    def test_whitespace_name_raises(self) -> None:
        with pytest.raises(ValueError, match="Name cannot be empty"):
            greet(name="   ")

    def test_zero_count_raises(self) -> None:
        with pytest.raises(ValueError, match="Count must be at least 1"):
            greet(name="World", count=0)

    def test_negative_count_raises(self) -> None:
        with pytest.raises(ValueError, match="Count must be at least 1"):
            greet(name="World", count=-1)

    def test_combined_options(self) -> None:
        result = greet(name="World", greeting="Hey", uppercase=True, count=2)
        assert result == "HEY, WORLD!\nHEY, WORLD!"


class TestProcessData:
    """Tests for the process_data function."""

    def test_process_json_file(self, tmp_json_file: Path) -> None:
        result = process_data(input_file=str(tmp_json_file))
        assert result["rows"] == 2
        assert result["destination"] == "stdout"

    def test_process_csv_file(self, tmp_csv_file: Path) -> None:
        result = process_data(input_file=str(tmp_csv_file))
        assert result["rows"] == 2

    def test_process_text_file(self, tmp_text_file: Path) -> None:
        result = process_data(input_file=str(tmp_text_file))
        assert result["rows"] == 3

    def test_process_with_json_output(
        self, tmp_json_file: Path, tmp_path: Path
    ) -> None:
        output = tmp_path / "out.json"
        result = process_data(
            input_file=str(tmp_json_file),
            output_file=str(output),
            output_format="json",
        )
        assert result["rows"] == 2
        assert output.exists()

    def test_process_with_csv_output(self, tmp_csv_file: Path, tmp_path: Path) -> None:
        output = tmp_path / "out.csv"
        result = process_data(
            input_file=str(tmp_csv_file),
            output_file=str(output),
            output_format="csv",
        )
        assert output.exists()

    def test_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError, match="Input file not found"):
            process_data(input_file="/nonexistent/file.txt")

    def test_unsupported_format_raises(self, tmp_text_file: Path) -> None:
        with pytest.raises(ValueError, match="Unsupported format"):
            process_data(input_file=str(tmp_text_file), output_format="xml")

    def test_json_output_content(self, tmp_json_file: Path, tmp_path: Path) -> None:
        output = tmp_path / "out.json"
        process_data(
            input_file=str(tmp_json_file),
            output_file=str(output),
            output_format="json",
        )
        with output.open() as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["name"] == "Alice"

    def test_text_output_to_file(self, tmp_text_file: Path, tmp_path: Path) -> None:
        out = tmp_path / "dump.txt"
        result = process_data(
            input_file=str(tmp_text_file),
            output_file=str(out),
            output_format="text",
        )
        assert result["destination"] == str(out)
        assert out.read_text().count("line") >= 1


class TestReadWriteHelpers:
    """Coverage for private I/O helpers."""

    def test_read_json_single_object_wraps_list(self, tmp_path: Path) -> None:
        p = tmp_path / "one.json"
        p.write_text('{"id": "1"}')
        rows = _read_rows(p)
        assert rows == [{"id": "1"}]

    def test_write_output_empty_list_json(self, tmp_path: Path) -> None:
        out = tmp_path / "empty.json"
        _write_output([], str(out), "json")
        assert json.loads(out.read_text()) == []


class TestBookingManager:
    """Tests for booking manager (non-interactive helpers)."""

    def test_init_rejects_non_positive_dimensions(self) -> None:
        with pytest.raises(ValueError, match="at least 1"):
            BookingManager(title="T", rows=0, seats_per_row=5)
        with pytest.raises(ValueError, match="at least 1"):
            BookingManager(title="T", rows=2, seats_per_row=0)

    def test_get_booking_missing_returns_none(self) -> None:
        manager = BookingManager(title="Test", rows=3, seats_per_row=5)
        assert manager.get_booking("GIC0001") is None

    def test_get_copy_all_bookings_matches_layout(self) -> None:
        manager = BookingManager(title="Test", rows=2, seats_per_row=4)
        snapshot = manager.get_copy_all_bookings()
        assert len(snapshot) == 2
        assert all(cell == "." for cell in snapshot[0])

    def test_confirm_booking_updates_map(self) -> None:
        manager = BookingManager(title="Test", rows=2, seats_per_row=3)
        seats = [(0, 0), (0, 1)]
        manager.confirm_booking(seats)
        assert manager.map[0][0] == "#"
        assert manager.map[0][1] == "#"
        manager.bookings["GIC0001"] = seats
        assert manager.get_booking("GIC0001") == seats

    def test_find_default_seats_skips_full_rows(self) -> None:
        manager = BookingManager(title="T", rows=2, seats_per_row=3)
        for c in range(3):
            manager.map[0][c] = "#"
        allocated, copy_map = manager.find_default_seats(2)
        assert len(allocated) == 2
        assert all(r == 1 for r, _ in allocated)
        assert copy_map[1][0] == "o"

    def test_find_default_seats_spans_rows_when_needed(self) -> None:
        manager = BookingManager(title="T", rows=2, seats_per_row=3)
        allocated, _ = manager.find_default_seats(5)
        assert len(allocated) == 5

    def test_find_default_seats_fills_left_after_right_side(self) -> None:
        """Cover the second inner loop when gaps remain after scanning right of start_col."""
        manager = BookingManager(title="T", rows=1, seats_per_row=5)
        manager.map[0][2] = "#"
        manager.map[0][3] = "#"
        allocated, copy_map = manager.find_default_seats(3)
        assert len(allocated) == 3
        assert copy_map[0][0] == "o" and copy_map[0][1] == "o" and copy_map[0][4] == "o"

    def test_find_custom_seats_overflow_uses_default_allocator(self) -> None:
        manager = BookingManager(title="T", rows=2, seats_per_row=2)
        seats = manager.find_custom_seats(0, 0, 3)
        assert len(seats) == 3
        assert manager.map[0][0] == "#" and manager.map[0][1] == "#"

    def test_find_custom_seats_stops_when_remaining_zero(self) -> None:
        manager = BookingManager(title="T", rows=2, seats_per_row=4)
        seats = manager.find_custom_seats(0, 0, 1)
        assert seats == [(0, 0)]

    def test_print_seats_writes_grid(self, capsys: pytest.CaptureFixture[str]) -> None:
        manager = BookingManager(title="T", rows=2, seats_per_row=2)
        manager.print_seats("x", 1, manager.get_copy_all_bookings())
        out = capsys.readouterr().out
        assert "Selected seats:" in out
        assert "SCREEN" in out.replace(" ", "")

    def test_get_valid_seat_no_accepts_free_seat(self) -> None:
        manager = BookingManager(title="T", rows=2, seats_per_row=3)
        assert manager.get_valid_seat_no("B2") == (1, 1)

    def test_get_valid_seat_no_retries_on_short_input(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manager = BookingManager(title="T", rows=2, seats_per_row=3)
        answers = iter(["x", "A1"])

        def fake_prompt(*_a: object, **_k: object) -> str:
            return next(answers)

        monkeypatch.setattr(click, "prompt", fake_prompt)
        assert manager.get_valid_seat_no("") == (0, 0)

    def test_get_valid_seat_no_retries_on_non_digit_suffix(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manager = BookingManager(title="T", rows=2, seats_per_row=3)
        answers = iter(["A1"])

        def fake_prompt(*_a: object, **_k: object) -> str:
            return next(answers)

        monkeypatch.setattr(click, "prompt", fake_prompt)
        assert manager.get_valid_seat_no("Axx") == (0, 0)

    def test_get_valid_seat_no_retries_on_out_of_range(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manager = BookingManager(title="T", rows=2, seats_per_row=3)
        answers = iter(["A1"])

        def fake_prompt(*_a: object, **_k: object) -> str:
            return next(answers)

        monkeypatch.setattr(click, "prompt", fake_prompt)
        assert manager.get_valid_seat_no("Z1") == (0, 0)

    def test_get_valid_seat_no_retries_when_seat_booked(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manager = BookingManager(title="T", rows=2, seats_per_row=3)
        manager.map[0][0] = "#"
        answers = iter(["A2"])

        def fake_prompt(*_a: object, **_k: object) -> str:
            return next(answers)

        monkeypatch.setattr(click, "prompt", fake_prompt)
        assert manager.get_valid_seat_no("A1") == (0, 1)

    def test_book_ticket_accepts_default_allocation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manager = BookingManager(title="Inception", rows=2, seats_per_row=5)
        monkeypatch.setattr(click, "prompt", lambda *a, **k: "")
        before = manager.available_tickets
        manager.book_ticket(1)
        assert manager.available_tickets == before - 1
        assert "GIC0001" in manager.bookings

    def test_book_ticket_custom_start_seat(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manager = BookingManager(title="T", rows=2, seats_per_row=4)
        monkeypatch.setattr(click, "prompt", lambda *a, **k: "A2")
        manager.book_ticket(1)
        assert manager.bookings["GIC0001"]
        assert manager.map[0][1] == "#"
