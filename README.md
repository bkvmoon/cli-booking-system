# GIC Cinemas Booking System

A CLI application for managing cinema seat bookings with intelligent seat allocation, following Python best practices for project structure, testing, and code quality.

## Project Structure

```
gic/
├── pyproject.toml                  # Project config, dependencies, tool settings
├── README.md
├── .gitignore
├── .env.example
├── src/
│   └── gic_cinema_booking/
│       ├── __init__.py             # Package version
│       ├── cli.py                  # CLI entry point (Click commands)
│       ├── services.py             # Business logic (separated from CLI)
│       ├── config.py               # Configuration from env vars
│       └── exceptions.py           # Custom exceptions
└── tests/
    ├── __init__.py
    ├── conftest.py                 # Shared fixtures
    ├── test_cli.py                 # CLI integration tests
    ├── test_services.py            # Unit tests for business logic
    ├── test_config.py              # Config tests
    └── test_exceptions.py          # Exception tests
```

## Best Practices Demonstrated

- **`src` layout** — Prevents accidental imports from the project root
- **Separation of concerns** — CLI layer (`cli.py`) vs business logic (`services.py`)
- **Type hints** — Full type annotations with `mypy` enforcement
- **Custom exceptions** — Structured error hierarchy with exit codes
- **Dataclass config** — Immutable config from environment variables
- **Click + Rich** — Composable CLI with beautiful terminal output
- **Pytest fixtures** — Reusable test fixtures in `conftest.py`
- **Parametrized testing** — Multiple scenarios per test class
- **Ruff** — Fast linting and formatting
- **Modern packaging** — `pyproject.toml` with `setuptools` build backend

## Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"
```

## Usage

Run the interactive cinema booking system:

```bash
gic
```

### Application Flow

**1. Initial Setup**
When the application starts, you'll be prompted to define the movie title and seating map in `[Title] [Row] [SeatsPerRow]` format:
- Maximum rows: 26
- Maximum seats per row: 50

```
Please define movie title and seating map in [Title] [Row] [SeatsPerRow] format:
> Inception 8 10
```

**2. Main Menu**
```
Welcome to GIC Cinemas
[1] Book tickets for Inception (80 seats available)
[2] Check bookings
[3] Exit
```

**3. Book Tickets (Option 1)**
- Enter the number of tickets to book
- Default seat allocation starts from the furthest row, middle column
- Overflow spills to the next row closer to the screen
- You can accept the default seats or specify a custom starting position (e.g., `B03`)
- A booking ID is generated (e.g., `GIC0001`)

**4. Check Bookings (Option 2)**
- Enter your booking ID to view the seating map
- Your booked seats are marked with `o`
- Other booked seats are marked with `#`

**5. Exit (Option 3)**
- Displays a thank you message and exits

### Seat Allocation Rules

**Default Selection:**
- Start from the furthest row from the screen
- Start from the middle-most possible column
- When a row cannot accommodate all tickets, overflow to the next row closer to the screen

**Custom Selection:**
- Starting from the specified position, fill empty seats to the right
- When insufficient seats in the row, overflow follows default selection rules

### Example Session

```
Please define movie title and seating map in [Title] [Row] [SeatsPerRow] format:
> Inception 8 10

Welcome to GIC Cinemas
[1] Book tickets for Inception (80 seats available)
[2] Check bookings
[3] Exit
Please enter your selection:
> 1

Enter number of tickets to book, or enter blank to go back to main menu:
> 4

Successfully reserved 4 Inception tickets.
Booking id: GIC0001
Selected seats:
          S C R E E N
--------------------------------
H .  .  .  .  .  .  .  .  .  .
...
A .  .  .  o  o  o  o  .  .  .
  1  2  3  4  5  6  7  8  9  10

Enter blank to accept seat selection, or enter new seating position:
> 

Booking id: GIC0001 confirmed.
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage (terminal summary)
pytest --cov=gic_cinema_booking --cov-report=term-missing

# HTML coverage report (open htmlcov/index.html in a browser)
pytest --cov=gic_cinema_booking --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_services.py

# Run specific test class
pytest tests/test_services.py::TestGreet

# Run with verbose output
pytest -v
```

## Code Quality

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
mypy src/
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CLI_APP_NAME` | GIC Cinemas | Application display name |
| `CLI_DEBUG` | false | Enable debug mode |
| `CLI_LOG_LEVEL` | INFO | Logging level |
| `CLI_DATA_DIR` | ./data | Data directory path |
| `CLI_MAX_RETRIES` | 3 | Max retry attempts |

Copy `.env.example` to `.env` and customize as needed.

## Coverage Report

Current test coverage: **94%** (294 statements, 18 missed)

```bash
pytest --cov=gic_cinema_booking --cov-report=html --cov-report=term-missing
open htmlcov/index.html
```
