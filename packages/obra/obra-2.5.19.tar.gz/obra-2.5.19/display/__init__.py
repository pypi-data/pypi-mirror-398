"""Display utilities for Obra using Rich console.

This module provides a configured Rich Console and error handling utilities.

Encoding Strategy (following Python best practices):
---------------------------------------------------
UTF-8 mode is enforced at CLI startup. This is the standard
approach used by major Python CLI tools (pip, poetry, black, etc.).

If encoding issues still occur despite UTF-8 enforcement, the
handle_encoding_errors decorator provides helpful guidance to users,
following Rich's own recommendation (GitHub Issue #212).

References:
- https://dev.to/methane/python-use-utf-8-mode-on-windows-212i
- https://peps.python.org/pep-0529/
- https://github.com/willmcgugan/rich/issues/212
"""

import functools
from collections.abc import Callable
from typing import Any, TypeVar

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Type variable for decorator
F = TypeVar("F", bound=Callable[..., Any])


def handle_encoding_errors(func: F) -> F:
    """Decorator to catch encoding errors with user-friendly messages.

    This follows Rich's recommended approach: when encoding fails,
    provide clear guidance on how to fix the environment rather than
    silently degrading functionality.

    Example:
        @app.command()
        @handle_encoding_errors
        def my_command():
            console.print("Starting...")
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except UnicodeEncodeError as e:
            # Use raw print to avoid any Rich formatting issues
            print("\n[ERROR] Terminal encoding issue detected.")
            print(f"        Character: {e.object[e.start:e.end]!r}")
            print("\nThis usually means your terminal is not configured for UTF-8.")
            print("\nSolutions:")
            print("  1. Use Windows Terminal (recommended) instead of cmd.exe")
            print("  2. Set environment variable: PYTHONUTF8=1")
            print("  3. Set environment variable: PYTHONIOENCODING=utf-8")
            print("  4. In cmd.exe, run: chcp 65001")
            print("\nFor more info: https://obra.dev/docs/troubleshooting/windows-unicode")

            # Import typer here to avoid circular imports
            import typer

            raise typer.Exit(1)

    return wrapper  # type: ignore[return-value]


# Module-level console instance
# Standard Rich Console - UTF-8 is enforced at CLI startup
console = Console()


def print_error(message: str, detail: str = "") -> None:
    """Print an error message with consistent styling.

    Args:
        message: Main error message
        detail: Optional additional detail
    """
    text = Text()
    text.append("Error: ", style="bold red")
    text.append(message)
    if detail:
        text.append(f"\n{detail}", style="dim")
    console.print(text)


def print_success(message: str) -> None:
    """Print a success message with consistent styling.

    Args:
        message: Success message to display
    """
    text = Text()
    text.append("Success: ", style="bold green")
    text.append(message)
    console.print(text)


def print_warning(message: str) -> None:
    """Print a warning message with consistent styling.

    Args:
        message: Warning message to display
    """
    text = Text()
    text.append("Warning: ", style="bold yellow")
    text.append(message)
    console.print(text)


def print_info(message: str) -> None:
    """Print an info message with consistent styling.

    Args:
        message: Info message to display
    """
    text = Text()
    text.append("Info: ", style="bold blue")
    text.append(message)
    console.print(text)


def print_panel(content: str, title: str = "", style: str = "blue") -> None:
    """Print content in a bordered panel.

    Args:
        content: Content to display inside panel
        title: Optional panel title
        style: Border style/color
    """
    panel = Panel(content, title=title, border_style=style)
    console.print(panel)


def create_table(title: str = "", show_header: bool = True) -> Table:
    """Create a styled table for consistent output.

    Args:
        title: Optional table title
        show_header: Whether to show column headers

    Returns:
        Configured Rich Table instance
    """
    return Table(
        title=title,
        show_header=show_header,
        header_style="bold cyan",
        border_style="blue",
    )


__all__ = [
    "console",
    "create_table",
    "handle_encoding_errors",
    "print_error",
    "print_info",
    "print_panel",
    "print_success",
    "print_warning",
]

# Re-export error display utilities for convenience
from obra.display.errors import (
    ERROR_CODE_MAP,
    ErrorDisplay,
    display_error,
    display_obra_error,
    get_error_display,
)

__all__ += [
    "ERROR_CODE_MAP",
    "ErrorDisplay",
    "display_error",
    "display_obra_error",
    "get_error_display",
]

# Re-export observability utilities for CLI commands
from obra.display.observability import (
    ObservabilityConfig,
    ProgressEmitter,
    VerbosityLevel,
)

__all__ += [
    "ObservabilityConfig",
    "ProgressEmitter",
    "VerbosityLevel",
]
