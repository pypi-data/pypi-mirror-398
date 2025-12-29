"""Exception classes for Obra."""


class ObraError(Exception):
    """Base exception for all Obra errors.

    All Obra exceptions include a `recovery` field with guidance on how to resolve
    the error. This helps both users and LLM agents understand the next steps.

    Attributes:
        recovery: Human-readable guidance on how to resolve this error
    """

    def __init__(self, message: str, recovery: str = "") -> None:
        """Initialize ObraError.

        Args:
            message: Error message describing what went wrong
            recovery: Guidance on how to resolve the error
        """
        super().__init__(message)
        self.recovery = recovery or "Check the error message and try again."


class APIError(ObraError):
    """Raised when Cloud Functions API call fails.

    Common causes:
    - Network connectivity issues
    - Invalid authentication token
    - Rate limit exceeded
    - Server-side errors

    Attributes:
        status_code: HTTP status code (0 if not applicable)
        response_body: Raw response body from server
        recovery: Guidance on how to resolve the error
    """

    def __init__(
        self,
        message: str,
        status_code: int = 0,
        response_body: str = "",
        recovery: str = "",
    ) -> None:
        """Initialize APIError.

        Args:
            message: Error message
            status_code: HTTP status code (0 if not applicable)
            response_body: Raw response body from server
            recovery: Guidance on how to resolve the error
        """
        if not recovery:
            recovery = self._default_recovery(status_code)
        super().__init__(message, recovery)
        self.status_code = status_code
        self.response_body = response_body

    @staticmethod
    def _default_recovery(status_code: int | None) -> str:
        """Generate default recovery guidance based on HTTP status code."""
        if status_code is None or status_code == 0:
            return "Check your network connection and try again."
        if status_code == 401:
            return "Run 'obra login' to sign in again."
        if status_code == 403:
            return "Access denied. Run 'obra login' to sign in or contact support."
        if status_code == 404:
            return "Resource not found. The session may have expired."
        if status_code == 429:
            return "Rate limit exceeded. Wait for reset or request a limit increase."
        if 500 <= status_code < 600:
            return "Server error. Try again in a few minutes."
        return "Check the error details and try again."


class ConfigurationError(ObraError):
    """Raised when configuration is invalid or missing.

    Common causes:
    - Configuration file not found
    - Not authenticated (no Firebase auth token)
    - Missing required fields
    - Terms not accepted

    Attributes:
        recovery: Guidance on how to resolve the error
    """

    def __init__(self, message: str, recovery: str = "") -> None:
        """Initialize ConfigurationError.

        Args:
            message: Error message
            recovery: Guidance on how to resolve the error
        """
        if not recovery:
            recovery = "Run 'obra login' to authenticate and configure the client."
        super().__init__(message, recovery)


class ExecutionError(ObraError):
    """Raised when LLM execution fails.

    Common causes:
    - LLM CLI not found (claude, gemini, or codex)
    - Process timeout
    - JSON parsing errors
    - Permission issues

    Attributes:
        exit_code: Process exit code
        stderr: Standard error output from process
        recovery: Guidance on how to resolve the error
    """

    def __init__(
        self,
        message: str,
        exit_code: int = 0,
        stderr: str = "",
        recovery: str = "",
    ) -> None:
        """Initialize ExecutionError.

        Args:
            message: Error message
            exit_code: Process exit code
            stderr: Standard error output from process
            recovery: Guidance on how to resolve the error
        """
        if not recovery:
            recovery = self._default_recovery(exit_code, message)
        super().__init__(message, recovery)
        self.exit_code = exit_code
        self.stderr = stderr

    @staticmethod
    def _default_recovery(exit_code: int, message: str) -> str:
        """Generate default recovery guidance based on error details."""
        msg_lower = message.lower()
        if "not found" in msg_lower or "no such file" in msg_lower:
            return "Install an LLM CLI: claude, gemini, or codex. Run 'obra health-check' for details."
        if "timeout" in msg_lower:
            return "The task may be too complex. Try breaking it into smaller steps."
        if "json" in msg_lower or "parse" in msg_lower:
            return "Output parsing failed. Run 'obra health-check' to verify installation."
        if exit_code == 1:
            return "Check the stderr output for details."
        if exit_code == 127:
            return "Command not found. Verify LLM CLI is installed and in PATH."
        return "Check 'obra health-check' for installation issues."


class AuthenticationError(ObraError):
    """Raised when authentication fails.

    Common causes:
    - User cancelled browser sign-in
    - Email not on beta allowlist
    - Invalid or expired token
    - Network error during auth

    Attributes:
        recovery: Guidance on how to resolve the error
    """

    def __init__(self, message: str, recovery: str = "") -> None:
        """Initialize AuthenticationError.

        Args:
            message: Error message
            recovery: Guidance on how to resolve the error
        """
        if not recovery:
            recovery = "Run 'obra login' to sign in again."
        super().__init__(message, recovery)


class TermsNotAcceptedError(APIError):
    """Raised when server rejects request due to terms not accepted.

    This is a specific 403 error indicating the user must run
    'obra login' to accept the Beta Software Agreement.

    Attributes:
        required_version: The terms version that must be accepted
        terms_url: URL to view the terms
        action: Suggested action to resolve the issue
        recovery: Guidance on how to resolve the error
    """

    def __init__(
        self,
        message: str = "Terms not accepted",
        required_version: str = "",
        terms_url: str = "https://obra.dev/terms",
        action: str = "Run 'obra login' to accept terms.",
    ) -> None:
        """Initialize TermsNotAcceptedError.

        Args:
            message: Error message from server
            required_version: The terms version that must be accepted
            terms_url: URL to view the terms
            action: Suggested action to resolve the issue
        """
        recovery = f"{action} View terms at: {terms_url}"
        super().__init__(
            message=message,
            status_code=403,
            response_body="",
            recovery=recovery,
        )
        self.required_version = required_version
        self.terms_url = terms_url
        self.action = action


class ConnectionError(ObraError):
    """Raised when Obra cannot connect to the server.

    Obra requires an internet connection for the hybrid architecture.
    This error is raised when the server is unreachable.

    Attributes:
        recovery: Guidance on how to resolve the error
    """

    def __init__(self, message: str = "") -> None:
        """Initialize ConnectionError.

        Args:
            message: Error message
        """
        default_msg = (
            "Obra requires an internet connection. "
            "Please check your network and try again."
        )
        super().__init__(message or default_msg, recovery="Check your network connection.")


class OrchestratorError(ObraError):
    """Raised when orchestration fails.

    This error is raised when the orchestration loop encounters
    an unrecoverable error.

    Attributes:
        session_id: Session ID if available
        recovery: Guidance on how to resolve the error
    """

    def __init__(self, message: str, session_id: str = "", recovery: str = "") -> None:
        """Initialize OrchestratorError.

        Args:
            message: Error message
            session_id: Session ID if available
            recovery: Recovery guidance
        """
        if session_id and not recovery:
            recovery = f"Try resuming with: obra resume --session-id {session_id}"
        super().__init__(message, recovery=recovery)
        self.session_id = session_id
