"""Business logic module for the GIC Cinemas booking system.

This module contains the core business logic separated from the CLI layer to
ensure testability. It includes the BookingManager class for managing movie seat
allocations, along with utility functions for data processing and greeting generation.
"""

from __future__ import annotations

import copy
import csv
import json
import logging
from pathlib import Path

import click

try:
    from rich.console import Console
except ModuleNotFoundError:

    class Console:  # type: ignore[no-redef]
        def print(self, message: str) -> None:
            print(message)


logger = logging.getLogger(__name__)


class BookingManager:
    """Manages in-memory seat bookings for movie theater reservations.

    This class handles the allocation and tracking of seat bookings for a movie
    theater. It provides methods for booking tickets with default or custom seat
    selection, validating seat numbers, and displaying seat maps. The seat map
    uses a grid system where rows are labeled A-Z and seats are numbered from 1.
    """

    def __init__(self, title: str, rows: int, seats_per_row: int) -> None:
        """Initialize a new BookingManager for a movie.

        Args:
            title: The name of the movie.
            rows: The number of rows in the theater (must be at least 1).
            seats_per_row: The number of seats per row (must be at least 1).

        Raises:
            ValueError: If rows or seats_per_row is less than 1.
        """
        logger.debug(
            f"Initializing BookingManager: title={title}, rows={rows}, seats_per_row={seats_per_row}"
        )
        if rows < 1 or seats_per_row < 1:
            logger.error(
                f"Invalid dimensions: rows={rows}, seats_per_row={seats_per_row}"
            )
            raise ValueError("Rows and seats per row must be at least 1")
        self.title = title
        self.rows = rows
        self.seats_per_row = seats_per_row
        self.available_tickets: int = rows * seats_per_row
        self.map = [["." for _ in range(seats_per_row)] for _ in range(rows)]
        self.bookings: dict[str, list[tuple[int, int]]] = {}
        self.console = Console()
        logger.info(
            f"BookingManager initialized with {self.available_tickets} total seats"
        )

    def get_booking(self, booking_id: str) -> list[tuple[int, int]] | None:
        """Retrieve the seat allocation for a given booking ID.

        Args:
            booking_id: The unique identifier for the booking.

        Returns:
            A list of (row, column) tuples representing the booked seats, or
            None if the booking ID does not exist.
        """
        return self.bookings.get(booking_id)

    def get_copy_all_bookings(self) -> list[list[str]]:
        """Return a deep copy of the current seat map.

        Returns:
            A 2D list representing the seat map where '.' indicates an
            available seat and '#' indicates a booked seat.
        """
        return copy.deepcopy(self.map)

    def book_ticket(self, tickets: int) -> None:
        """Allocate seats for a ticket booking interactively.

        This method prompts the user to either accept the default seat allocation
        or specify a custom starting seat. It validates the seat selection and
        records the booking with a generated booking ID.

        Args:
            tickets: The number of tickets to book.

        Raises:
            ValueError: If the seat selection is invalid or seats are unavailable.
        """
        logger.debug(f"Starting booking process for {tickets} tickets")

        while True:
            allocated, copy_map = self.find_default_seats(tickets)
            booking_id = f"GIC{len(self.bookings) + 1:04d}"
            logger.debug(
                f"Generated booking ID: {booking_id}, allocated seats: {allocated}"
            )
            print(f"Successfully reserved {tickets} {self.title} tickets.")
            print(f"Booking id: {booking_id} {self.title} tickets.")
            self.print_seats(booking_id, tickets, copy_map)

            selected_seat = click.prompt(
                click.style(
                    "Enter blank to accept seat selection, or enter new seating position",
                    fg="cyan",
                ),
                default="",
                show_default=False,
            ).strip()
            logger.debug(f"User seat selection: '{selected_seat}'")

            if not selected_seat:
                logger.debug("User accepted default seats")
                self.confirm_booking(allocated)
                self.bookings[booking_id] = allocated
                self.available_tickets -= tickets
                logger.info(
                    f"Booking {booking_id} confirmed with {len(allocated)} seats, {self.available_tickets} remaining"
                )
                print(f"Booking id: {booking_id} confirmed.")
                break

            logger.debug(f"User requested custom seat: {selected_seat}")
            start_row, start_col = self.get_valid_seat_no(selected_seat)
            allocated = self.find_custom_seats(start_row, start_col, tickets)
            self.bookings[booking_id] = allocated
            self.available_tickets -= tickets
            logger.info(
                f"Booking {booking_id} confirmed with custom seats, {self.available_tickets} remaining"
            )
            print(f"Booking id: {booking_id} confirmed.")
            break

    def get_valid_seat_no(self, selected_seat: str) -> tuple[int, int]:
        """Validate and convert a seat identifier to row and column indices.

        This method prompts the user repeatedly until a valid seat identifier
        is provided. The seat identifier must be in the format like 'A1', 'B5', etc.
        where the letter represents the row (A-Z) and the number represents
        the seat number (1-based).

        Args:
            selected_seat: The initial seat identifier to validate.

        Returns:
            A tuple of (row_index, column_index) representing the seat location.

        Raises:
            ValueError: If the seat format is invalid or the seat is out of range.
        """
        logger.debug(f"Validating seat: {selected_seat}")
        while True:
            if len(selected_seat) < 2:
                logger.warning(f"Invalid seat format (too short): {selected_seat}")
                self.console.print(click.style("Invalid choice.", fg="yellow"))
                selected_seat = click.prompt(
                    click.style("Please enter valid seat no", fg="yellow"),
                    default="",
                    show_default=False,
                ).strip()
                continue
            start_row = ord(selected_seat[0].upper()) - 65
            seat_num_text = selected_seat[1:]
            if not seat_num_text.isdigit():
                logger.warning(
                    f"Invalid seat format (non-numeric suffix): {selected_seat}"
                )
                self.console.print(
                    click.style(
                        "Invalid choice. Please enter valid seat no.", fg="yellow"
                    )
                )
                selected_seat = click.prompt(
                    click.style("Please enter valid seat no", fg="yellow"),
                    default="",
                    show_default=False,
                ).strip()
                continue
            start_col = int(seat_num_text) - 1
            logger.debug(f"Parsed seat: row={start_row}, col={start_col}")
            if (
                start_row < 0
                or start_row >= self.rows
                or start_col < 0
                or start_col >= self.seats_per_row
            ):
                logger.warning(
                    f"Seat out of range: row={start_row} (max {self.rows - 1}), col={start_col} (max {self.seats_per_row - 1})"
                )
                self.console.print(
                    click.style(
                        "Invalid choice. Please enter valid seat no.", fg="yellow"
                    )
                )
                selected_seat = click.prompt(
                    click.style("Please enter valid seat no", fg="yellow"),
                    default="",
                    show_default=False,
                ).strip()
                continue
            if self.map[start_row][start_col] == "#":
                logger.warning(f"Seat already booked: {selected_seat}")
                self.console.print(
                    click.style(
                        f"Seat {selected_seat} is already booked. Please enter valid seat no.",
                        fg="yellow",
                    )
                )
                selected_seat = click.prompt(
                    click.style("Please enter valid seat no", fg="yellow"),
                    default="",
                    show_default=False,
                ).strip()
                continue

            logger.debug(f"Valid seat confirmed: ({start_row}, {start_col})")
            return start_row, start_col

    def find_default_seats(
        self, tickets: int
    ) -> tuple[list[tuple[int, int]], list[list[str]]]:
        """Find the optimal default seat allocation for a given number of tickets.

        This method allocates seats starting from the center of the theater,
        working outward to the sides, and filling rows from back to front.
        This provides the best viewing experience for groups.

        Args:
            tickets: The number of seats to allocate.

        Returns:
            A tuple containing:
                - A list of (row, column) tuples for the allocated seats.
                - A copy of the seat map with allocated seats marked as 'o'.
        """
        logger.debug(f"Finding default seats for {tickets} tickets")
        allocated = []
        remaining = tickets
        copy_map = copy.deepcopy(self.map)
        for r in range(self.rows):
            if remaining <= 0:
                logger.debug(f"All {tickets} seats allocated")
                break

            available_in_row = [
                c for c in range(self.seats_per_row) if self.map[r][c] == "."
            ]
            logger.debug(
                f"Row {r}: {len(available_in_row)} available seats, need {remaining}"
            )

            if not available_in_row:
                logger.debug(f"Row {r} is full, skipping")
                continue

            if len(available_in_row) >= remaining:
                start_col = (self.seats_per_row - remaining) // 2
                logger.debug(f"Row {r} has enough seats, starting from col {start_col}")
                for c in range(start_col, self.seats_per_row):
                    if remaining > 0 and copy_map[r][c] == ".":
                        copy_map[r][c] = "o"
                        allocated.append((r, c))
                        remaining -= 1
                for c in range(start_col):
                    if remaining > 0 and copy_map[r][c] == ".":
                        allocated.append((r, c))
                        copy_map[r][c] = "o"
                        remaining -= 1
            else:
                logger.debug(f"Row {r} has {len(available_in_row)} seats, taking all")
                for c in available_in_row:
                    allocated.append((r, c))
                    copy_map[r][c] = "o"
                    remaining -= 1

        logger.debug(f"Default allocation complete: {allocated}")
        return allocated, copy_map

    def confirm_booking(self, allocated_seats: list[tuple[int, int]]) -> None:
        """Mark the allocated seats as booked in the seat map.

        Args:
            allocated_seats: A list of (row, column) tuples to mark as booked.

        Returns:
            None
        """
        logger.debug(f"Confirming booking for seats: {allocated_seats}")
        for r, c in allocated_seats:
            self.map[r][c] = "#"
        logger.debug("Seat map updated after confirmation")

    def find_custom_seats(
        self, start_row: int, start_col: int, tickets: int
    ) -> list[tuple[int, int]]:
        """Find seats starting from a custom position for a given number of tickets.

        This method allocates seats starting from the specified position and
        moving right within the same row. If insufficient seats are available
        in the row, it uses the default allocation method for the remaining tickets.

        Args:
            start_row: The row index to start allocation from.
            start_col: The column index to start allocation from.
            tickets: The number of seats to allocate.

        Returns:
            A list of (row, column) tuples for the allocated seats.
        """
        logger.debug(
            f"Finding custom seats from ({start_row}, {start_col}) for {tickets} tickets"
        )
        allocated: list[tuple[int, int]] = []
        remaining = tickets
        for c in range(start_col, self.seats_per_row):
            if remaining > 0 and self.map[start_row][c] == ".":
                self.map[start_row][c] = "#"
                allocated.append((start_row, c))
                remaining -= 1
            elif remaining == 0:
                break

        if remaining > 0:
            logger.debug(
                f"Need {remaining} more seats, using default allocation for overflow"
            )
            overflow_allocated, _ = self.find_default_seats(remaining)
            self.confirm_booking(overflow_allocated)
            allocated.extend(overflow_allocated)

        logger.debug(f"Custom allocation complete: {allocated}")
        return allocated

    def print_seats(
        self, _booking_id: str, _tickets: int, copy_map: list[list[str]]
    ) -> None:
        """Display the seat map with booked seats highlighted.

        This method prints a visual representation of the theater seating
        arrangement, showing the screen at the top and marking booked seats
        with '#' and selected seats with 'o'.

        Args:
            _booking_id: The booking ID (unused in current implementation).
            _tickets: The number of tickets (unused in current implementation).
            copy_map: The seat map to display.

        Returns:
            None
        """
        print("Selected seats:")
        print("S C R E E N".center(self.seats_per_row * 3))
        print("-" * (self.seats_per_row * 3))
        for r in reversed(range(self.rows)):
            print(f"{chr(65 + r)}", end="  ")
            for c in range(self.seats_per_row):
                print(f"{copy_map[r][c]}", end="  ")
            print()
        print(end="   ")
        for c in range(self.seats_per_row):
            print(f"{c + 1}", end="  ")
        print()


def greet(
    name: str, greeting: str = "Hello", uppercase: bool = False, count: int = 1
) -> str:
    """Generate a greeting message.

    Args:
        name: The name to greet.
        greeting: The greeting word to use.
        uppercase: Whether to uppercase the output.
        count: Number of times to repeat the greeting.

    Returns:
        The formatted greeting string.

    Raises:
        ValueError: If count is less than 1 or name is empty.
    """
    if not name.strip():
        raise ValueError("Name cannot be empty")
    if count < 1:
        raise ValueError("Count must be at least 1")

    message = f"{greeting}, {name}!"
    if uppercase:
        message = message.upper()

    return "\n".join([message] * count)


def process_data(
    input_file: str,
    output_file: str | None = None,
    output_format: str = "text",
) -> dict[str, str | int]:
    """Process data from an input file.

    Args:
        input_file: Path to the input file.
        output_file: Optional path for output file.
        output_format: Output format (json, csv, text).

    Returns:
        Dict with 'rows' count and 'destination' path.

    Raises:
        FileNotFoundError: If input_file does not exist.
        ValueError: If output_format is not supported.
    """
    path = Path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    supported_formats = {"json", "csv", "text"}
    if output_format not in supported_formats:
        raise ValueError(
            f"Unsupported format: {output_format}. Use one of {supported_formats}"
        )

    rows = _read_rows(path)
    destination = _write_output(rows, output_file, output_format)

    return {"rows": len(rows), "destination": destination}


def _read_rows(path: Path) -> list[dict[str, str]]:
    """Read rows from a file (supports JSON and CSV).

    Args:
        path: Path to the input file.

    Returns:
        List of row dictionaries.
    """
    suffix = path.suffix.lower()

    if suffix == ".json":
        with path.open() as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
    elif suffix == ".csv":
        with path.open(newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
    else:
        with path.open() as f:
            return [{"line": line.strip()} for line in f if line.strip()]


def _write_output(
    rows: list[dict[str, str]], output_file: str | None, output_format: str
) -> str:
    """Write processed data to output.

    Args:
        rows: Data rows to write.
        output_file: Optional output file path.
        output_format: Format to write in.

    Returns:
        Destination description string.
    """
    if output_file is None:
        return "stdout"

    out_path = Path(output_file)

    if output_format == "json":
        with out_path.open("w") as f:
            json.dump(rows, f, indent=2)
    elif output_format == "csv":
        if rows:
            with out_path.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
    else:
        with out_path.open("w") as f:
            for row in rows:
                f.write(f"{row}\n")

    return str(out_path)
