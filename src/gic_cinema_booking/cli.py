"""Command-line interface for the GIC Cinemas booking system.

This module provides the CLI entry point using the Click framework. It handles
interactive menu navigation for movie ticket booking, including seat map definition,
ticket booking, and booking lookup functionality.
"""

import logging

import click

try:
    from rich.console import Console
except ModuleNotFoundError:

    class Console:  # type: ignore[no-redef]
        def print(self, message: str) -> None:
            print(message)


from gic_cinema_booking import __version__
from gic_cinema_booking.config import Config
from gic_cinema_booking.services import BookingManager

console = Console()

# Configure logging
config = Config.from_env()
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if config.debug
    else "%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="gic")
@click.pass_context
def app(ctx: click.Context) -> None:
    """Main entry point for the GIC Cinemas booking system.

    This command group serves as the primary entry point for the CLI. If no
    subcommand is provided, it launches the interactive menu for booking tickets.

    Args:
        ctx: The Click context object for command execution.

    Returns:
        None
    """
    logger.debug(
        f"Starting GIC Cinemas Booking System v{__version__} (debug={config.debug})"
    )
    if ctx.invoked_subcommand is None:
        _run_interactive_menu()


def _run_interactive_menu() -> None:
    """Run the interactive menu for defining movie title and seating map.

    This function prompts the user to enter the movie title and seating layout
    in the format [Title] [Row] [SeatsPerRow]. It validates the input to ensure
    the number of rows does not exceed 26 and seats per row does not exceed 50.
    Once valid input is received, it creates a BookingManager instance and
    delegates to the main menu options.

    Returns:
        None
    """
    logger.debug("Starting interactive menu")
    while True:
        seat_map_input = click.prompt(
            click.style(
                "Please define movie title and seating map in [Title] [Row] [SeatsPerRow] format",
                fg="cyan",
            ),
            default="",
            show_default=False,
        ).strip()
        logger.debug(f"User input: {seat_map_input}")
        if seat_map_input == "":
            logger.debug("Empty input, continuing loop")
            continue

        parts = seat_map_input.split()
        if len(parts) != 3:
            logger.warning(f"Invalid input format: {seat_map_input}")
            console.print("[red]Error:[/red] Please provide exactly [red]3[/red] values.")
            continue

        movie_title = parts[0]
        try:
            rows = int(parts[1])
            seats_per_row = int(parts[2])
            logger.debug(
                f"Parsed: title={movie_title}, rows={rows}, seats_per_row={seats_per_row}"
            )
            if rows > 26:
                logger.warning(f"Rows exceed limit: {rows}")
                console.print(
                    "[red]Error:[/red] Maximum rows allowed [red]26[/red]. Please enter less than [red]26[/red]"
                )
                continue

            if seats_per_row > 50:
                logger.warning(f"Seats per row exceed limit: {seats_per_row}")
                console.print(
                    "[red]Error:[/red] Maximum seats per row allowed [red]50[/red]. Please enter less than[red]50[/red]"
                )
                continue

            bookings = BookingManager(
                title=movie_title, rows=rows, seats_per_row=seats_per_row
            )
            logger.debug(
                f"Created BookingManager for {movie_title} with {rows * seats_per_row} seats"
            )
        except ValueError as e:
            logger.error(f"Value error parsing input: {e}")
            console.print(f"[red]Error:[/red] {e}")
            continue

        _interactive_menu_options(bookings)
        return


def _interactive_menu_options(bookings: BookingManager) -> None:
    """Display and handle the main menu options for the booking system.

    This function presents the user with three options: book tickets, check
    bookings, or exit. It loops until the user selects exit (option 3). Blank
    input is ignored and the menu is redisplayed.

    Args:
        bookings: The BookingManager instance containing the current state.

    Returns:
        None
    """
    logger.debug(f"Entering main menu for {bookings.title}")
    while True:
        console.print("\n[bold cyan]Welcome to GIC Cinemas[/bold cyan]")
        console.print(
            f"[1] Book tickets for {bookings.title} ({bookings.available_tickets} seats available)"
        )
        console.print("[2] Check bookings")
        console.print("[3] Exit")
        choice = click.prompt(
            click.style("Please enter your selection", fg="cyan"),
            default="",
            show_default=False,
        ).strip()
        logger.debug(f"Menu selection: {choice}")

        if choice == "":
            logger.debug("Empty selection, continuing loop")
            continue
        if choice == "1":
            logger.debug("User selected Book tickets")
            _interactive_book_tickets(bookings)
        elif choice == "2":
            logger.debug("User selected Check bookings")
            _interactive_check_bookings(bookings)
        elif choice == "3":
            logger.debug("User selected Exit")
            console.print("[green]Thank you for using GIC Cinemas system. Bye![/green]")
            return
        else:
            logger.warning(f"Invalid menu choice: {choice}")
            console.print("[yellow]Invalid choice. Please select 1, 2, or 3.[/yellow]")


def _interactive_book_tickets(bookings: BookingManager) -> None:
    """Handle the interactive ticket booking flow.

    This function prompts the user for the number of tickets to book. It validates
    that the input is a valid number and that sufficient seats are available.
    If validation passes, it delegates to the BookingManager to process the booking.
    Blank input returns to the main menu.

    Args:
        bookings: The BookingManager instance to handle the booking.

    Returns:
        None
    """
    logger.debug("Entering ticket booking flow")
    while True:
        tickets = click.prompt(
            click.style(
                "Enter number of tickets to book, or enter blank to go back to main menu",
                fg="cyan",
            ),
            default="",
            show_default=False,
        ).strip()
        logger.debug(f"Ticket input: {tickets}")
        if not tickets:
            logger.debug("Empty ticket input, returning to menu")
            return

        if not tickets.isdigit():
            logger.debug(f"Invalid ticket number: {tickets}")
            console.print(
                f"[red]Enter a valid number of tickets "
                f"({bookings.available_tickets} seats available).[/red]"
            )
            continue

        if int(tickets) > bookings.available_tickets:
            logger.debug(
                f"Requested tickets {tickets} exceed available {bookings.available_tickets}"
            )
            console.print(
                f"[red]Sorry, there are only {bookings.available_tickets} seat(s) available.[/red]"
            )
            continue

        try:
            logger.debug(f"Booking {tickets} tickets for {bookings.title}")
            bookings.book_ticket(tickets=int(tickets))
            logger.debug("Booking completed successfully")
            return
        except ValueError as e:
            logger.error(f"Booking failed: {e}")
            console.print(f"[red]Error:[/red] {e}")
            return


def _interactive_check_bookings(bookings: BookingManager) -> None:
    """Handle the interactive booking lookup flow.

    This function prompts the user for a booking ID and displays the seat map
    with the booked seats marked. If the booking ID is invalid, an error message
    is displayed and the user is prompted again. Blank input returns to the main menu.

    Args:
        bookings: The BookingManager instance containing the booking data.

    Returns:
        None
    """
    logger.debug("Entering booking check flow")
    while True:
        booking_id = click.prompt(
            click.style(
                "Enter booking id, or enter blank to go back to main menu", fg="cyan"
            ),
            default="",
            show_default=False,
        ).strip()
        logger.debug(f"Booking ID input: {booking_id}")
        if booking_id == "":
            logger.debug("Empty booking ID, returning to menu")
            return

        try:
            allocated = bookings.get_booking(booking_id)
            logger.debug(f"Retrieved booking: {booking_id}, seats: {allocated}")
            if not allocated:
                logger.warning(f"Booking not found: {booking_id}")
                console.print(f"[red]Invalid booking id: {booking_id}.[/red]")
                continue

            seat_map = bookings.get_copy_all_bookings()
            for r in range(bookings.rows):
                for c in range(bookings.seats_per_row):
                    if (r, c) not in allocated and seat_map[r][c] == "#":
                        seat_map[r][c] = "o"

            logger.debug(f"Displaying booking {booking_id} with {len(allocated)} seats")
            console.print(
                click.style(f"[bold]Booking id:[/bold] {booking_id}", fg="cyan")
            )
            bookings.print_seats(booking_id, len(allocated), seat_map)
            break
        except ValueError as e:
            logger.error(f"Error checking booking: {e}")
            console.print(f"[red]Error:[/red] {e}")
