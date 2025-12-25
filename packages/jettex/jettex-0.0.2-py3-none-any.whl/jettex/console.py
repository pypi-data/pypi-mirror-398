"""Centralized console and logging for jettex.

This module provides:
- Rich Console for formatted terminal output
- Python logging integration with Rich handlers
- Verbosity level management (quiet, normal, verbose)
- Progress bars, spinners, panels, and tables
- Optional file logging
"""

import logging
from enum import IntEnum
from pathlib import Path
from typing import Optional, Iterator, List, Dict, Any
from contextlib import contextmanager

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme


# Custom theme for jettex
JETTEX_THEME = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red bold",
    "package": "magenta",
    "path": "blue underline",
    "command": "cyan bold",
    "dim": "dim",
})


class Verbosity(IntEnum):
    """Verbosity levels for output."""
    QUIET = 0    # Only errors
    NORMAL = 1   # Info and above
    VERBOSE = 2  # Debug and above


# Module-level state
_console: Optional[Console] = None
_verbosity: Verbosity = Verbosity.NORMAL
_logger: Optional[logging.Logger] = None


def get_console() -> Console:
    """Get or create the Rich console instance."""
    global _console
    if _console is None:
        _console = Console(theme=JETTEX_THEME)
    return _console


def setup_logging(
    verbosity: Verbosity = Verbosity.NORMAL,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """Configure logging with Rich integration.

    Args:
        verbosity: Output verbosity level
        log_file: Optional path to write debug logs

    Returns:
        Configured logger for jettex
    """
    global _verbosity, _logger

    _verbosity = verbosity

    # Create logger
    logger = logging.getLogger("jettex")
    logger.handlers.clear()

    # Set base level to DEBUG (filtering happens at handler level)
    logger.setLevel(logging.DEBUG)

    # Console handler with Rich formatting
    console = get_console()

    # Map verbosity to logging level for console
    console_level = {
        Verbosity.QUIET: logging.ERROR,
        Verbosity.NORMAL: logging.INFO,
        Verbosity.VERBOSE: logging.DEBUG,
    }[verbosity]

    rich_handler = RichHandler(
        console=console,
        show_time=verbosity == Verbosity.VERBOSE,
        show_path=verbosity == Verbosity.VERBOSE,
        rich_tracebacks=True,
        tracebacks_show_locals=verbosity == Verbosity.VERBOSE,
        markup=True,
    )
    rich_handler.setLevel(console_level)
    logger.addHandler(rich_handler)

    # File handler (always DEBUG level)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """Get the jettex logger, setting up with defaults if needed."""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger


def is_quiet() -> bool:
    """Check if quiet mode is active."""
    return _verbosity == Verbosity.QUIET


def is_verbose() -> bool:
    """Check if verbose mode is active."""
    return _verbosity == Verbosity.VERBOSE


# --- Rich Output Helpers ---

def print_success(message: str, title: str = "Success") -> None:
    """Print a success panel."""
    if is_quiet():
        return
    console = get_console()
    console.print(Panel(message, title=f"[green]{title}[/green]", border_style="green"))


def print_error(message: str, title: str = "Error") -> None:
    """Print an error panel."""
    console = get_console()
    console.print(Panel(message, title=f"[red]{title}[/red]", border_style="red"))


def print_warning(message: str) -> None:
    """Print a warning message."""
    if is_quiet():
        return
    console = get_console()
    console.print(f"[warning]Warning:[/warning] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    if is_quiet():
        return
    console = get_console()
    console.print(f"[info]{message}[/info]")


# --- Progress Indicators ---

class _DummyProgress:
    """Dummy progress object for quiet mode."""
    def add_task(self, *args: Any, **kwargs: Any) -> int:
        return 0
    def update(self, *args: Any, **kwargs: Any) -> None:
        pass
    def __enter__(self) -> "_DummyProgress":
        return self
    def __exit__(self, *args: Any) -> None:
        pass


@contextmanager
def download_progress(description: str = "Downloading") -> Iterator[Progress]:
    """Context manager for download progress bar.

    Yields a Progress object. Use task = progress.add_task() to create task,
    then progress.update(task, advance=bytes) to update.
    """
    if is_quiet():
        yield _DummyProgress()  # type: ignore
        return

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=get_console(),
        transient=True,
    )
    with progress:
        yield progress


@contextmanager
def spinner(message: str) -> Iterator[None]:
    """Context manager for a spinner during long operations.

    Usage:
        with spinner("Compiling document..."):
            do_compilation()
    """
    if is_quiet():
        yield
        return

    console = get_console()
    with console.status(message, spinner="dots"):
        yield


@contextmanager
def step_progress(description: str = "Working") -> Iterator[Progress]:
    """Context manager for step-based progress (not download).

    Yields a Progress object for tracking discrete steps.
    """
    if is_quiet():
        yield _DummyProgress()  # type: ignore
        return

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=get_console(),
        transient=True,
    )
    with progress:
        yield progress


# --- Tables ---

def create_table(title: str, columns: List[tuple]) -> Table:
    """Create a Rich table with standard styling.

    Args:
        title: Table title
        columns: List of (name, style) tuples

    Returns:
        Configured Table object
    """
    table = Table(title=title, show_header=True, header_style="bold")
    for name, style in columns:
        table.add_column(name, style=style)
    return table


def print_table(table: Table) -> None:
    """Print a table to the console."""
    if is_quiet():
        return
    get_console().print(table)


# --- Package Display ---

def print_package_list(packages: List[str], title: str = "Packages") -> None:
    """Print a list of packages in a formatted table."""
    if is_quiet():
        return

    if not packages:
        print_info("No packages found.")
        return

    table = create_table(title, [("Package", "package")])
    for pkg in packages:
        table.add_row(pkg)

    print_table(table)
    print_info(f"{len(packages)} packages total.")


def print_package_info(info: Dict[str, Any], name: str = "Package Info") -> None:
    """Print package info in a formatted panel."""
    if is_quiet():
        return

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold cyan")
    table.add_column("Value")

    for key, value in info.items():
        display_key = key.replace("_", " ").replace("-", " ").title()
        table.add_row(display_key, str(value))

    get_console().print(Panel(table, title=name))


def print_search_results(results: List[Dict[str, Any]]) -> None:
    """Print search results in a formatted table."""
    if is_quiet():
        return

    if not results:
        print_info("No packages found.")
        return

    table = create_table("Search Results", [
        ("Package", "package"),
        ("File", "dim"),
    ])

    for r in results:
        table.add_row(r.get("package", ""), r.get("file", ""))

    print_table(table)


def print_tinytex_info(root: Path, version: str) -> None:
    """Print TinyTeX installation info."""
    if is_quiet():
        return

    table = Table(show_header=False, box=None)
    table.add_column("Key", style="bold")
    table.add_column("Value", style="path")

    table.add_row("TinyTeX Root", str(root))
    table.add_row("Version", version)

    get_console().print(Panel(table, title="TinyTeX Information"))


def print_compile_result(success: bool, output_file: Optional[Path], stderr: str = "") -> None:
    """Print compilation result."""
    if success:
        msg = f"Output: [path]{output_file}[/path]"
        print_success(msg, title="Compilation Successful")
    else:
        error_msg = "Compilation failed."
        if stderr:
            # Truncate long errors
            truncated = stderr[:1000] + "..." if len(stderr) > 1000 else stderr
            error_msg += f"\n\n[dim]{truncated}[/dim]"
        print_error(error_msg, title="Compilation Failed")
