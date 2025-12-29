"""Base classes for Hybrid Orchestrator handlers.

This module provides base classes and mixins for handler implementations.

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md Section 2
    - obra/hybrid/orchestrator.py
    - obra/hybrid/handlers/fix.py
"""

from pathlib import Path


class ObservabilityContextMixin:
    """Mixin for handlers that need observability context propagation.

    This mixin provides attributes and methods for passing observability context
    (session ID, log file, etc.) to subprocess agents via environment variables.

    ## Architecture Context (ISSUE-OBS-003)

    Uses OpenTelemetry/CI-CD pattern for cross-process context propagation:
    - OBRA_SESSION_ID: Session ID for trace correlation (like OTEL_TRACE_ID)
    - OBRA_LOG_FILE: Log file path for event emission (like span exporter)
    - OBRA_ORCHESTRATOR_MODE: Mode identifier for agent detection
    - OBRA_WORKING_DIR: Working directory for file operations

    ## Usage

    Handler classes should inherit from this mixin and set the optional
    attributes during initialization:

        >>> class MyHandler(ObservabilityContextMixin):
        ...     def __init__(self, working_dir: Path, session_id: Optional[str] = None):
        ...         self._working_dir = working_dir
        ...         self._session_id = session_id
        ...         self._log_file = None
        ...
        ...     def deploy_agent(self, prompt: str):
        ...         env = self._get_observability_env()
        ...         # Pass env to subprocess

    Attributes:
        _session_id: Optional session ID for trace correlation
        _log_file: Optional log file path for event emission
    """

    _session_id: str | None = None
    _log_file: Path | None = None

    def _get_observability_env(self) -> dict[str, str]:
        """Build observability environment variables for subprocess agents.

        Returns a dictionary of environment variables to be merged with os.environ
        when spawning subprocess agents. These variables enable cross-process
        observability context propagation.

        Returns:
            Dictionary of environment variables with observability context.
            Always includes OBRA_ORCHESTRATOR_MODE and OBRA_WORKING_DIR.
            Conditionally includes OBRA_SESSION_ID and OBRA_LOG_FILE if set.

        Example:
            >>> handler._session_id = "session-123"
            >>> handler._log_file = Path("/tmp/obra.log")
            >>> handler._working_dir = Path("/home/user/project")
            >>> env_vars = handler._get_observability_env()
            >>> print(env_vars)
            {
                'OBRA_SESSION_ID': 'session-123',
                'OBRA_LOG_FILE': '/tmp/obra.log',
                'OBRA_ORCHESTRATOR_MODE': 'hybrid',
                'OBRA_WORKING_DIR': '/home/user/project'
            }
        """
        env: dict[str, str] = {}

        # Session ID for trace correlation (like OTEL_TRACE_ID)
        if self._session_id:
            env["OBRA_SESSION_ID"] = self._session_id

        # Log file path for event emission (like span exporter)
        if self._log_file:
            env["OBRA_LOG_FILE"] = str(self._log_file)

        # Orchestrator mode for agent detection (always set)
        env["OBRA_ORCHESTRATOR_MODE"] = "hybrid"

        # Working directory for file operations (always set)
        if hasattr(self, "_working_dir"):
            env["OBRA_WORKING_DIR"] = str(self._working_dir)

        return env


__all__ = ["ObservabilityContextMixin"]
