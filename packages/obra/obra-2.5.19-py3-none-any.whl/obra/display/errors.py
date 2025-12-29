"""Error UX mapping for user-friendly error messages per PRD Pre-Implementation #3.

Maps error codes to user-friendly messages and recovery actions.
This module ensures consistent error handling across all CLI commands.

Reference: docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md Section "Pre-Implementation Requirements #3"
"""

from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from obra.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    ExecutionError,
    ObraError,
    OrchestratorError,
    TermsNotAcceptedError,
)


@dataclass
class ErrorDisplay:
    """Structured error display information."""

    code: str
    title: str
    message: str
    recovery: str
    details: str | None = None


# Error code mappings from PRD Pre-Implementation #3
ERROR_CODE_MAP: dict[str, ErrorDisplay] = {
    "SESSION_NOT_FOUND": ErrorDisplay(
        code="SESSION_NOT_FOUND",
        title="Session Not Found",
        message="Session not found. It may have expired or been completed.",
        recovery="Run 'obra run \"<objective>\"' to start a new session.",
    ),
    "SESSION_EXPIRED": ErrorDisplay(
        code="SESSION_EXPIRED",
        title="Session Expired",
        message="Session expired after 24 hours of inactivity.",
        recovery="Run 'obra run \"<objective>\"' to start a new session.",
    ),
    "RATE_LIMITED": ErrorDisplay(
        code="RATE_LIMITED",
        title="Rate Limit Reached",
        message="Rate limit reached. Try again in {retry_after} seconds.",
        recovery="Wait for the specified time and try again.",
    ),
    "INVALID_STATE": ErrorDisplay(
        code="INVALID_STATE",
        title="Invalid State",
        message="Cannot {action} - session is in {state} state.",
        recovery="Run 'obra status' to check current state.",
    ),
    "SERVER_ERROR": ErrorDisplay(
        code="SERVER_ERROR",
        title="Server Error",
        message="Server error. Your work is saved.",
        recovery="Run 'obra resume {session_id}' to continue.",
    ),
    "NETWORK_ERROR": ErrorDisplay(
        code="NETWORK_ERROR",
        title="Connection Lost",
        message="Connection lost. Your work is saved locally.",
        recovery="Check network and try again. Run 'obra doctor' to diagnose.",
    ),
    "AUTH_EXPIRED": ErrorDisplay(
        code="AUTH_EXPIRED",
        title="Authentication Expired",
        message="Session expired. Run 'obra login' to re-authenticate.",
        recovery="Run 'obra login' to sign in again.",
    ),
    "AUTH_REQUIRED": ErrorDisplay(
        code="AUTH_REQUIRED",
        title="Authentication Required",
        message="You must be logged in to use this command.",
        recovery="Run 'obra login' to sign in.",
    ),
    "TERMS_NOT_ACCEPTED": ErrorDisplay(
        code="TERMS_NOT_ACCEPTED",
        title="Terms Not Accepted",
        message="You must accept the beta terms to continue.",
        recovery="Run 'obra setup' to accept terms and configure your environment.",
    ),
    "INVALID_CONFIG": ErrorDisplay(
        code="INVALID_CONFIG",
        title="Invalid Configuration",
        message="Configuration is invalid or missing.",
        recovery="Run 'obra config' to review and fix configuration.",
    ),
    "LLM_NOT_FOUND": ErrorDisplay(
        code="LLM_NOT_FOUND",
        title="LLM CLI Not Found",
        message="No LLM CLI found (claude, gemini, or codex).",
        recovery="Install an LLM CLI and ensure it's in PATH.",
    ),
    "EXECUTION_TIMEOUT": ErrorDisplay(
        code="EXECUTION_TIMEOUT",
        title="Execution Timeout",
        message="The task took too long to complete.",
        recovery="Rerun with --stream flag, or break into smaller steps.",
    ),
    "VERSION_MISMATCH": ErrorDisplay(
        code="VERSION_MISMATCH",
        title="Version Mismatch",
        message="Client version is not compatible with server.",
        recovery="Run 'pip install --upgrade obra' to update.",
    ),
    "BETA_ACCESS_DENIED": ErrorDisplay(
        code="BETA_ACCESS_DENIED",
        title="Beta Access Required",
        message="Your email is not on the beta allowlist.",
        recovery="Request access at obra.dev/beta or contact support.",
    ),
}


def get_error_display(error_code: str, **kwargs: str) -> ErrorDisplay:
    """Get error display for an error code.

    Args:
        error_code: The error code to look up
        **kwargs: Placeholders to substitute in message/recovery

    Returns:
        ErrorDisplay with formatted message and recovery
    """
    display = ERROR_CODE_MAP.get(error_code)
    if not display:
        return ErrorDisplay(
            code=error_code or "UNKNOWN_ERROR",
            title="Error",
            message=kwargs.get("message", "An unexpected error occurred."),
            recovery=kwargs.get("recovery", "Please try again or contact support."),
        )

    # Format placeholders
    message = display.message
    recovery = display.recovery
    for key, value in kwargs.items():
        message = message.replace(f"{{{key}}}", str(value))
        recovery = recovery.replace(f"{{{key}}}", str(value))

    return ErrorDisplay(
        code=display.code,
        title=display.title,
        message=message,
        recovery=recovery,
        details=kwargs.get("details"),
    )


def exception_to_error_code(exc: Exception) -> str:
    """Map exception type to error code.

    Args:
        exc: The exception to map

    Returns:
        Error code string
    """
    if isinstance(exc, TermsNotAcceptedError):
        return "TERMS_NOT_ACCEPTED"
    if isinstance(exc, AuthenticationError):
        return "AUTH_REQUIRED"
    if isinstance(exc, ConnectionError):
        return "NETWORK_ERROR"
    if isinstance(exc, ConfigurationError):
        return "INVALID_CONFIG"
    if isinstance(exc, APIError):
        status_code = getattr(exc, "status_code", 0)
        if status_code == 401:
            return "AUTH_EXPIRED"
        if status_code == 403:
            return "BETA_ACCESS_DENIED"
        if status_code == 404:
            return "SESSION_NOT_FOUND"
        if status_code == 409:
            return "INVALID_STATE"
        if status_code == 410:
            return "SESSION_EXPIRED"
        if status_code == 429:
            return "RATE_LIMITED"
        if status_code >= 500:
            return "SERVER_ERROR"
    elif isinstance(exc, ExecutionError):
        message_lower = str(exc).lower()
        if "not found" in message_lower:
            return "LLM_NOT_FOUND"
        if "timeout" in message_lower:
            return "EXECUTION_TIMEOUT"
    elif isinstance(exc, OrchestratorError):
        return "SERVER_ERROR"

    return "UNKNOWN_ERROR"


def display_error(exc: Exception, console: Console | None = None) -> None:
    """Display an error with user-friendly formatting.

    Args:
        exc: The exception to display
        console: Optional Rich Console (uses default if not provided)
    """
    if console is None:
        console = Console()

    error_code = exception_to_error_code(exc)

    # Build kwargs from exception attributes
    kwargs: dict[str, str] = {
        "message": str(exc),
    }

    # Extract session_id if available
    if hasattr(exc, "session_id") and exc.session_id:
        kwargs["session_id"] = exc.session_id

    # Extract retry_after from rate limit responses
    if hasattr(exc, "response_body"):
        try:
            import json

            body = json.loads(exc.response_body)
            if "retry_after" in body:
                kwargs["retry_after"] = str(body["retry_after"])
        except (json.JSONDecodeError, TypeError):
            pass

    # Extract recovery from exception if available
    if hasattr(exc, "recovery") and exc.recovery:
        kwargs["recovery"] = exc.recovery

    display = get_error_display(error_code, **kwargs)

    # Build error panel
    content = Text()
    content.append(display.message, style="white")

    if display.details:
        content.append(f"\n\n{display.details}", style="dim")

    content.append(f"\n\n{display.recovery}", style="cyan")

    panel = Panel(
        content,
        title=f"[bold red]{display.title}[/bold red]",
        title_align="left",
        border_style="red",
        padding=(1, 2),
    )

    console.print()
    console.print(panel)


def display_obra_error(error: ObraError, console: Console | None = None) -> None:
    """Display an ObraError with its built-in recovery guidance.

    All ObraError subclasses include recovery guidance. This function
    displays both the error and the recovery action.

    Args:
        error: The ObraError to display
        console: Optional Rich Console (uses default if not provided)
    """
    if console is None:
        console = Console()

    error_code = exception_to_error_code(error)
    display = get_error_display(error_code)

    # Build error panel
    content = Text()
    content.append(str(error), style="white")

    # Use error's built-in recovery if available, otherwise use mapped recovery
    recovery = error.recovery if hasattr(error, "recovery") and error.recovery else display.recovery
    content.append(f"\n\n{recovery}", style="cyan")

    panel = Panel(
        content,
        title=f"[bold red]{display.title}[/bold red]",
        title_align="left",
        border_style="red",
        padding=(1, 2),
    )

    console.print()
    console.print(panel)


__all__ = [
    "ERROR_CODE_MAP",
    "ErrorDisplay",
    "display_error",
    "display_obra_error",
    "exception_to_error_code",
    "get_error_display",
]
