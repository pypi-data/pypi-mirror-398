"""Hybrid Orchestrator for EPIC-HYBRID-001.

This module provides the client-side orchestration logic for the Unified Hybrid Architecture.
It connects to the server, dispatches actions to appropriate handlers, and manages the
orchestration loop.

Design Principle (from PRD):
    - Server owns the brain (decisions, orchestration logic)
    - Client owns the hands (execution, code access)

The HybridOrchestrator:
    1. Starts a session with the server
    2. Receives action instructions from the server
    3. Dispatches to appropriate handlers (derive, examine, revise, execute, review, fix)
    4. Reports results back to the server
    5. Repeats until completion or escalation

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md Section 3
    - obra/api/protocol.py
    - obra/hybrid/handlers/*.py
"""

import hashlib
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Optional: ProductionLogger for observability (ISSUE-OBS-002)
# Not available in published obra package, only in development
try:
    from src.monitoring.production_logger import ProductionLogger
except ImportError:
    ProductionLogger = None  # type: ignore

from obra.api import APIClient
from obra.api.protocol import (
    ActionType,
    CompletionNotice,
    DerivedPlan,
    DeriveRequest,
    EscalationNotice,
    ExaminationReport,
    ExamineRequest,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    FixRequest,
    ResumeContext,
    ReviewRequest,
    RevisedPlan,
    RevisionRequest,
    ServerAction,
    SessionPhase,
    SessionStart,
    UserDecision,
    UserDecisionChoice,
)
from obra.config import get_max_iterations
from obra.display import console, print_info, print_warning
from obra.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    OrchestratorError,
)

logger = logging.getLogger(__name__)


class HybridOrchestrator:
    """Client-side orchestrator for Obra hybrid architecture.

    ## Architecture

    This orchestrator implements the **client-side** of the Obra SaaS hybrid
    architecture (ADR-027):

    - **Server**: Provides orchestration decisions, action instructions, and validation
    - **Client**: Builds prompts locally, executes LLM/agents, reports results

    ## Handler Responsibilities

    Each handler (`DeriveHandler`, `ExamineHandler`, etc.) implements client-side logic:
    1. Receives action request from server (objective, plan items, issues, etc.)
    2. Builds prompts entirely client-side
    3. Gathers tactical context locally (files, git, errors)
    4. Invokes LLM or agent locally
    5. Reports results back to server for validation

    Note: The marker-based prompt enrichment described in ADR-027 is an aspirational
    design. The current implementation builds prompts entirely client-side.

    ## Privacy Model

    Tactical context (file contents, git messages, errors) stays client-side.
    Server never receives file contents or local project details.

    See: docs/decisions/ADR-027-two-tier-prompting-architecture.md
    """

    def __init__(
        self,
        client: APIClient,
        working_dir: Path | None = None,
        on_progress: Callable[[str, dict[str, Any]], None] | None = None,
        on_escalation: Callable[[EscalationNotice], UserDecisionChoice] | None = None,
        on_stream: Callable[[str, str], None] | None = None,
    ) -> None:
        """Initialize HybridOrchestrator.

        Args:
            client: APIClient for server communication
            working_dir: Working directory for file operations
            on_progress: Optional callback for progress updates (action, payload)
            on_escalation: Optional callback for handling escalations
            on_stream: Optional callback for LLM streaming chunks (event_type, content)
        """
        self._client = client
        self._working_dir = working_dir or Path.cwd()
        self._session_id: str | None = None
        self._on_progress = on_progress
        self._on_escalation = on_escalation
        self._on_stream = on_stream

        # Handler registry - lazily initialized
        self._handlers: dict[ActionType, Any] = {}

        # LLM config - set by from_config() or defaults to None
        self._llm_config: dict[str, Any] | None = None

        # Phase tracking for observability (S3.T3)
        self._current_phase: SessionPhase | None = None
        self._phase_start_time: float | None = None

        # Polling failure tracking for diagnostics
        self._polling_failure_count: int = 0
        self._last_item_id: str | None = None

        # ISSUE-OBS-002: Initialize ProductionLogger for hybrid mode observability
        self._production_logger = self._init_production_logger()

        logger.debug(f"HybridOrchestrator initialized for {self._working_dir}")

    def _init_production_logger(self) -> Any:
        """Initialize ProductionLogger for hybrid mode observability (ISSUE-OBS-002).

        Uses separate log file (hybrid.jsonl) from standalone CLI (production.jsonl)
        to avoid confusion and enable parallel dobra/obra sessions.

        Returns:
            ProductionLogger instance or None if initialization fails or unavailable
        """
        # ProductionLogger not available in published package
        if ProductionLogger is None:
            logger.debug("ProductionLogger not available (development-only feature)")
            return None

        try:
            # Get runtime directory from environment or use default
            runtime_dir = Path(os.environ.get("OBRA_RUNTIME_DIR", "~/obra-runtime")).expanduser()
            log_file = runtime_dir / "logs" / "hybrid.jsonl"

            # Create minimal config for ProductionLogger
            # Match standalone CLI config structure from config/default_config.yaml
            config = {
                "path": str(log_file),
                "events": {
                    "user_input": True,
                    "nl_results": False,  # Not used in hybrid mode
                    "execution_results": True,
                    "errors": True,
                    "orchestrator_prompts": False,
                    "implementer_responses": False,
                },
                "privacy": {
                    "redact_pii": True,
                    "redact_secrets": True,
                },
                "rotation": {
                    "max_file_size_mb": 100,
                    "max_files": 10,
                },
                "flush": {
                    "immediate": True,  # Flush immediately for real-time monitoring
                },
            }

            prod_logger = ProductionLogger(config)
            logger.debug(f"ProductionLogger initialized for hybrid mode: {log_file}")
            return prod_logger

        except Exception as e:
            logger.warning(f"Failed to initialize ProductionLogger for hybrid mode: {e}")
            return None

    def _log_session_event(self, event_type: str, **kwargs) -> None:
        """Log hybrid session event to production logger (ISSUE-OBS-002).

        Args:
            event_type: Event type (session_started, derivation_started, etc.)
            **kwargs: Event-specific data
        """
        if self._production_logger and self._session_id:
            try:
                # Use ProductionLogger's internal _log_event method
                # This follows the established pattern from standalone CLI
                self._production_logger._log_event(
                    event_type,
                    self._session_id,
                    **kwargs
                )
            except Exception as e:
                logger.warning(f"Failed to log hybrid event '{event_type}': {e}")

    @classmethod
    def from_config(
        cls,
        working_dir: Path | None = None,
        on_progress: Callable[[str, dict[str, Any]], None] | None = None,
        on_escalation: Callable[[EscalationNotice], UserDecisionChoice] | None = None,
        on_stream: Callable[[str, str], None] | None = None,
        impl_provider: str | None = None,
        impl_model: str | None = None,
        thinking_level: str | None = None,
    ) -> "HybridOrchestrator":
        """Create HybridOrchestrator from configuration.

        Loads APIClient from ~/.obra/client-config.yaml.

        Args:
            working_dir: Working directory for file operations
            on_progress: Optional progress callback
            on_escalation: Optional escalation callback
            on_stream: Optional streaming callback for LLM output
            impl_provider: Optional implementation provider override (S5.T1)
            impl_model: Optional implementation model override (S5.T1)
            thinking_level: Optional thinking level override (S5.T1)

        Returns:
            Configured HybridOrchestrator

        Raises:
            ConfigurationError: If configuration is invalid or missing
        """
        try:
            client = APIClient.from_config()
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(f"Failed to create API client: {e}")

        # S5.T2: Resolve LLM config with overrides
        from obra.config import resolve_llm_config

        llm_config = resolve_llm_config(
            role="implementation",
            override_provider=impl_provider,
            override_model=impl_model,
            override_thinking_level=thinking_level,
        )

        orchestrator = cls(
            client=client,
            working_dir=working_dir,
            on_progress=on_progress,
            on_escalation=on_escalation,
            on_stream=on_stream,
        )

        # S5.T2: Store resolved config for handler creation
        orchestrator._llm_config = llm_config

        return orchestrator

    @property
    def client(self) -> APIClient:
        """Get the API client."""
        return self._client

    @property
    def working_dir(self) -> Path:
        """Get the working directory."""
        return self._working_dir

    @property
    def session_id(self) -> str | None:
        """Get the current session ID."""
        return self._session_id

    def is_online(self) -> bool:
        """Check if the server is reachable.

        Returns:
            True if server is reachable, False otherwise.
        """
        try:
            self._client.health_check()
            return True
        except ConnectionError as e:
            logger.warning("Health check failed: Network connectivity issue - %s", e)
            return False
        except AuthenticationError as e:
            logger.warning("Health check failed: Authentication error - %s", e)
            return False
        except ConfigurationError as e:
            logger.warning("Health check failed: Configuration error - %s", e)
            return False
        except APIError as e:
            if e.status_code == 401:
                logger.warning("Health check failed: Authentication invalid (401) - %s", e)
            elif e.status_code == 403:
                logger.warning("Health check failed: Access forbidden (403) - %s", e)
            else:
                logger.warning(
                    "Health check failed: API error (status %s) - %s",
                    e.status_code or "unknown",
                    e,
                )
            return False
        except Exception as e:
            logger.warning(
                "Health check failed: Unexpected error (%s) - %s",
                type(e).__name__,
                e,
            )
            return False

    def _ensure_online(self) -> None:
        """Ensure server is reachable.

        Raises:
            ConnectionError: If server is not reachable
        """
        if not self.is_online():
            raise ConnectionError()

    def _hash_working_dir(self) -> str:
        """Create SHA256 hash of working directory path.

        Returns:
            SHA256 hex digest of working directory path
        """
        return hashlib.sha256(str(self._working_dir).encode()).hexdigest()

    def _apply_resolved_llm_config(self, metadata: dict[str, Any]) -> dict[str, str] | None:
        """Apply server-resolved LLM config to local runtime settings."""
        resolved = metadata.get("resolved_llm_config")
        if not isinstance(resolved, dict):
            return None
        if self._llm_config is None:
            self._llm_config = {}
        for key in ("provider", "model", "thinking_level"):
            value = resolved.get(key)
            if value:
                self._llm_config[key] = value
        return {
            "provider": self._llm_config.get("provider", ""),
            "model": self._llm_config.get("model", ""),
            "thinking_level": self._llm_config.get("thinking_level", ""),
        }

    def _get_project_context(self) -> dict[str, Any]:
        """Gather minimal project context (no code content).

        Returns:
            Dictionary with project context (languages, frameworks, etc.)
        """
        context: dict[str, Any] = {
            "languages": [],
            "frameworks": [],
            "has_tests": False,
            "file_count": 0,
        }

        # Detect languages by file extensions
        extensions = set()
        file_count = 0
        try:
            for path in self._working_dir.rglob("*"):
                if path.is_file() and not any(
                    part.startswith(".") for part in path.parts
                ):
                    file_count += 1
                    if path.suffix:
                        extensions.add(path.suffix.lower())
        except Exception:
            pass  # Permission errors, etc.

        context["file_count"] = file_count

        # Map extensions to languages
        ext_to_lang = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
        }
        context["languages"] = list({ext_to_lang.get(ext) for ext in extensions if ext in ext_to_lang})

        # Detect common test directories
        test_dirs = ["tests", "test", "__tests__", "spec"]
        context["has_tests"] = any((self._working_dir / d).is_dir() for d in test_dirs)

        # Detect frameworks by config files
        framework_files = {
            "package.json": ["node"],
            "requirements.txt": ["python"],
            "pyproject.toml": ["python"],
            "Cargo.toml": ["rust"],
            "go.mod": ["go"],
            "pom.xml": ["java", "maven"],
            "build.gradle": ["java", "gradle"],
            "Gemfile": ["ruby"],
            "composer.json": ["php"],
        }
        for filename, frameworks in framework_files.items():
            if (self._working_dir / filename).exists():
                context["frameworks"].extend(frameworks)

        context["frameworks"] = list(set(context["frameworks"]))

        return context

    def _emit_progress(self, action: str, payload: dict[str, Any]) -> None:
        """Emit progress update.

        Args:
            action: Action being performed
            payload: Action payload
        """
        if self._on_progress:
            try:
                self._on_progress(action, payload)
            except Exception as e:
                logger.warning(
                    f"Progress callback failed for action '{action}': {e}",
                    exc_info=True
                )

    def _poll_with_backoff(
        self,
        poll_count: int,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        multiplier: float = 2.0,
    ) -> float:
        """Calculate and execute exponential backoff delay for polling.

        Implements exponential backoff: delay = base_delay * (multiplier ^ poll_count)
        capped at max_delay.

        Args:
            poll_count: Current poll iteration (0-indexed)
            base_delay: Initial delay in seconds (default: 1.0)
            max_delay: Maximum delay in seconds (default: 30.0)
            multiplier: Exponential multiplier (default: 2.0)

        Returns:
            The actual delay used in seconds
        """
        import time

        # Calculate delay with exponential backoff: 1, 2, 4, 8, 16, 30, 30...
        delay = min(base_delay * (multiplier ** poll_count), max_delay)
        time.sleep(delay)

        logger.debug(f"Polling wait: {delay:.1f}s (poll #{poll_count + 1})")
        return delay

    def _action_to_phase(self, action: ActionType) -> SessionPhase | None:
        """Map action type to session phase.

        Args:
            action: Action type from server

        Returns:
            Corresponding session phase, or None for non-phase actions
        """
        phase_mapping = {
            ActionType.DERIVE: SessionPhase.DERIVATION,
            ActionType.EXAMINE: SessionPhase.REFINEMENT,
            ActionType.REVISE: SessionPhase.REFINEMENT,
            ActionType.EXECUTE: SessionPhase.EXECUTION,
            ActionType.REVIEW: SessionPhase.REVIEW,
        }
        return phase_mapping.get(action)

    def _emit_phase_event(self, action: ActionType) -> None:
        """Emit phase transition events based on action.

        Tracks phase changes and emits phase_started/phase_completed events
        via the on_progress callback.

        Args:
            action: Current action type
        """
        import time

        new_phase = self._action_to_phase(action)
        if new_phase is None:
            return  # Skip non-phase actions (COMPLETE, ESCALATE, etc.)

        # Check if phase changed
        if new_phase != self._current_phase:
            # Emit phase_completed for previous phase
            if self._current_phase is not None and self._phase_start_time is not None:
                duration_ms = int((time.time() - self._phase_start_time) * 1000)
                self._emit_progress(
                    "phase_completed",
                    {
                        "phase": self._current_phase.value,
                        "duration_ms": duration_ms,
                    },
                )
                # ISSUE-OBS-002: Log phase_completed to production logger
                self._log_session_event(
                    "phase_completed",
                    phase=self._current_phase.value,
                    duration_ms=duration_ms,
                )

            # Emit phase_started for new phase
            self._current_phase = new_phase
            self._phase_start_time = time.time()
            self._emit_progress(
                "phase_started",
                {
                    "phase": new_phase.value,
                },
            )
            # ISSUE-OBS-002: Log phase_started to production logger
            self._log_session_event(
                "phase_started",
                phase=new_phase.value,
            )

    def _get_handler(self, action: ActionType) -> Any:
        """Get handler for action type.

        Lazily imports and instantiates handlers.

        Args:
            action: Action type

        Returns:
            Handler instance

        Raises:
            OrchestratorError: If handler not found
            ConfigurationError: If llm_config is invalid or missing required keys
        """
        if action not in self._handlers:
            # Validate llm_config for handlers that require it (C11)
            # DERIVE, EXAMINE, REVISE, EXECUTE, and FIX all need llm_config
            if action in (
                ActionType.DERIVE,
                ActionType.EXAMINE,
                ActionType.REVISE,
                ActionType.EXECUTE,
                ActionType.FIX,
            ):
                if self._llm_config is None:
                    raise ConfigurationError(
                        f"Cannot create {action.value} handler: llm_config is None. "
                        f"LLM configuration is required for {action.value} actions.",
                        recovery="Run 'obra config' to set up LLM configuration or use 'obra derive' with --model and --provider flags.",
                    )

                # Validate required keys
                required_keys = {"provider"}
                missing_keys = required_keys - set(self._llm_config.keys())
                if missing_keys:
                    raise ConfigurationError(
                        f"Cannot create {action.value} handler: llm_config missing required keys: {missing_keys}. "
                        f"Current config: {self._llm_config}",
                        recovery="Run 'obra config' to set up LLM configuration or use 'obra derive' with --model and --provider flags.",
                    )
            # Import handlers lazily to avoid circular imports
            if action == ActionType.DERIVE:
                from obra.hybrid.handlers.derive import DeriveHandler
                # S3.T6: Pass on_stream callback to handler
                # S4.T2: Pass llm_config to handler
                self._handlers[action] = DeriveHandler(
                    self._working_dir,
                    on_stream=self._on_stream,
                    llm_config=self._llm_config,
                    log_event=self._log_session_event,
                )
            elif action == ActionType.EXAMINE:
                from obra.hybrid.handlers.examine import ExamineHandler
                # S3.T6: Pass on_stream callback to handler
                # S4.T3: Pass llm_config to handler
                self._handlers[action] = ExamineHandler(
                    self._working_dir,
                    on_stream=self._on_stream,
                    llm_config=self._llm_config,
                    log_event=self._log_session_event,
                )
            elif action == ActionType.REVISE:
                from obra.hybrid.handlers.revise import ReviseHandler
                # S3.T6: Pass on_stream callback to handler
                # S4.T4: Pass llm_config to handler
                self._handlers[action] = ReviseHandler(
                    self._working_dir,
                    on_stream=self._on_stream,
                    llm_config=self._llm_config,
                    log_event=self._log_session_event,
                )
            elif action == ActionType.EXECUTE:
                from obra.hybrid.handlers.execute import ExecuteHandler
                # S5.T3: Pass llm_config to ExecuteHandler
                # ISSUE-OBS-003: Pass observability context for cross-process propagation
                log_file = Path(os.environ.get("OBRA_RUNTIME_DIR", "~/obra-runtime")).expanduser() / "logs" / "production.jsonl"
                self._handlers[action] = ExecuteHandler(
                    self._working_dir,
                    llm_config=self._llm_config,
                    session_id=self._session_id,
                    log_file=log_file,
                )
            elif action == ActionType.REVIEW:
                from obra.hybrid.handlers.review import ReviewHandler
                self._handlers[action] = ReviewHandler(self._working_dir)
            elif action == ActionType.FIX:
                from obra.hybrid.handlers.fix import FixHandler
                # ISSUE-OBS-003: Pass observability context for cross-process propagation
                log_file = Path(os.environ.get("OBRA_RUNTIME_DIR", "~/obra-runtime")).expanduser() / "logs" / "production.jsonl"
                self._handlers[action] = FixHandler(
                    self._working_dir,
                    llm_config=self._llm_config,
                    session_id=self._session_id,
                    log_file=log_file,
                )
            else:
                raise OrchestratorError(
                    f"No handler for action: {action.value}",
                    session_id=self._session_id or "",
                )

        return self._handlers[action]

    def _handle_action(self, server_action: ServerAction) -> dict[str, Any]:
        """Handle a server action by dispatching to appropriate handler.

        Args:
            server_action: Server action to handle

        Returns:
            Result to report back to server

        Raises:
            OrchestratorError: If action handling fails
        """
        action = server_action.action
        payload = server_action.payload

        logger.info(f"Handling action: {action.value} (iteration {server_action.iteration})")

        # S3.T3: Emit phase transition events
        self._emit_phase_event(action)

        self._emit_progress(action.value, payload)

        # Handle special actions
        if action == ActionType.COMPLETE:
            completion_notice = CompletionNotice.from_payload(payload)
            return {"completed": True, "notice": completion_notice}

        if action == ActionType.ESCALATE:
            escalation_notice = EscalationNotice.from_payload(payload)
            return self._handle_escalation(escalation_notice)

        if action == ActionType.ERROR:
            error_msg = server_action.error_message or "Unknown server error"
            error_code = server_action.error_code or "UNKNOWN"
            raise OrchestratorError(
                f"Server error [{error_code}]: {error_msg}",
                session_id=self._session_id or "",
            )

        if action == ActionType.WAIT:
            # Server is processing async, wait and poll
            return {"waiting": True}

        # Get handler for action
        handler = self._get_handler(action)

        # Create typed request from payload and dispatch to handler
        if action == ActionType.DERIVE:
            derive_req = DeriveRequest.from_payload(payload)
            # ISSUE-OBS-002: Log derivation_started event
            self._log_session_event(
                "derivation_started",
                objective=derive_req.objective,
                plan_id=getattr(derive_req, "plan_id", None),
            )
            result = handler.handle(derive_req)
            # ISSUE-OBS-002: Log derivation_complete event
            self._log_session_event(
                "derivation_complete",
                plan_items_count=len(result.get("plan_items", [])),
            )
            return result
        if action == ActionType.EXAMINE:
            examine_req = ExamineRequest.from_payload(payload)
            return handler.handle(examine_req)
        if action == ActionType.REVISE:
            revise_req = RevisionRequest.from_payload(payload)
            return handler.handle(revise_req)
        if action == ActionType.EXECUTE:
            execute_req = ExecutionRequest.from_payload(payload)
            if execute_req.current_item and execute_req.current_item.get("id"):
                self._last_item_id = execute_req.current_item.get("id")

            # Compatibility: some server versions return ActionType.EXECUTE with fix payload
            # (item_id + issues_to_fix) instead of ActionType.FIX. Route to FixHandler but report as FIX.
            if execute_req.current_item is None and payload.get("issues_to_fix"):
                fix_handler = self._get_handler(ActionType.FIX)
                fix_req = FixRequest.from_payload(payload)
                fix_result = fix_handler.handle(fix_req)
                fix_result["_report_as"] = ActionType.FIX.value
                return fix_result

            # S3.T5: Emit item_started event
            if execute_req.current_item:
                self._emit_progress("item_started", {"item": execute_req.current_item})
                # ISSUE-OBS-002: Log item_started to production logger
                self._log_session_event(
                    "item_started",
                    item=execute_req.current_item,
                )

            result = handler.handle(execute_req)

            # S3.T5: Emit item_completed event
            if execute_req.current_item:
                self._emit_progress(
                    "item_completed",
                    {"item": execute_req.current_item, "result": result},
                )
                # ISSUE-OBS-002: Log item_completed to production logger
                self._log_session_event(
                    "item_completed",
                    item=execute_req.current_item,
                    status=result.get("status", "unknown"),
                    files_changed=result.get("files_changed", 0),
                )

            return result
        if action == ActionType.REVIEW:
            review_payload = payload
            if not payload.get("item_id") and self._last_item_id:
                review_payload = dict(payload)
                review_payload["item_id"] = self._last_item_id
            review_req = ReviewRequest.from_payload(review_payload)
            if review_req.item_id:
                self._last_item_id = review_req.item_id
            return handler.handle(review_req)
        if action == ActionType.FIX:
            fix_payload = payload
            if not payload.get("item_id") and self._last_item_id:
                fix_payload = dict(payload)
                fix_payload["item_id"] = self._last_item_id
            fix_req = FixRequest.from_payload(fix_payload)
            if fix_req.item_id:
                self._last_item_id = fix_req.item_id
            return handler.handle(fix_req)
        raise OrchestratorError(
            f"Unhandled action: {action.value}",
            session_id=self._session_id or "",
        )

    def _handle_escalation(self, notice: EscalationNotice) -> dict[str, Any]:
        """Handle escalation by prompting user.

        Args:
            notice: Escalation notice from server

        Returns:
            User decision result
        """
        # If callback provided, use it
        if self._on_escalation:
            decision = self._on_escalation(notice)
            return {
                "escalation_id": notice.escalation_id,
                "decision": decision.value,
                "reason": "",
            }

        # Default: display and force complete
        print_warning(f"Escalation: {notice.reason.value}")

        # Defensive check for blocking_issues structure
        blocking_issues = notice.blocking_issues
        if not isinstance(blocking_issues, list):
            logger.warning(
                f"Invalid blocking_issues type: expected list, got {type(blocking_issues).__name__}. "
                f"Converting to empty list."
            )
            blocking_issues = []
        else:
            # Ensure all items are dicts
            validated_issues = []
            for idx, issue in enumerate(blocking_issues):
                if not isinstance(issue, dict):
                    logger.warning(
                        f"Invalid blocking_issue at index {idx}: expected dict, got {type(issue).__name__}. "
                        f"Skipping item."
                    )
                else:
                    validated_issues.append(issue)
            blocking_issues = validated_issues

        console.print(f"  Blocking issues: {len(blocking_issues)}")
        for issue in blocking_issues[:5]:  # Show first 5
            console.print(f"    - {issue.get('description', 'Unknown')}")

        return {
            "escalation_id": notice.escalation_id,
            "decision": UserDecisionChoice.FORCE_COMPLETE.value,
            "reason": "Auto-completed (no interactive handler)",
        }

    def _report_result(
        self,
        action: ActionType,
        result: dict[str, Any],
    ) -> ServerAction:
        """Report action result to server.

        Args:
            action: Action that was handled
            result: Result from handler

        Returns:
            Next server action
        """
        if not self._session_id:
            raise OrchestratorError("No active session")

        try:
            if action == ActionType.DERIVE:
                response = self._client._request(
                    "POST",
                    "report_derivation",
                    json=DerivedPlan(
                        session_id=self._session_id,
                        plan_items=result.get("plan_items", []),
                        raw_response=result.get("raw_response", ""),
                    ).to_dict(),
                )
            elif action == ActionType.EXAMINE:
                response = self._client._request(
                    "POST",
                    "report_examination",
                    json=ExaminationReport(
                        session_id=self._session_id,
                        iteration=result.get("iteration", 0),
                        issues=result.get("issues", []),
                        thinking_budget_used=result.get("thinking_budget_used", 0),
                        thinking_fallback=result.get("thinking_fallback", False),
                        raw_response=result.get("raw_response", ""),
                    ).to_dict(),
                )
            elif action == ActionType.REVISE:
                response = self._client._request(
                    "POST",
                    "report_revision",
                    json=RevisedPlan(
                        session_id=self._session_id,
                        plan_items=result.get("plan_items", []),
                        changes_summary=result.get("changes_summary", ""),
                        raw_response=result.get("raw_response", ""),
                    ).to_dict(),
                )
            elif action == ActionType.EXECUTE:
                response = self._client._request(
                    "POST",
                    "report_execution",
                    json=ExecutionResult(
                        session_id=self._session_id,
                        item_id=result.get("item_id", ""),
                        status=ExecutionStatus(result.get("status", "failure")),
                        summary=result.get("summary", ""),
                        files_changed=result.get("files_changed", 0),
                        tests_passed=result.get("tests_passed", False),
                        test_count=result.get("test_count", 0),
                        coverage_delta=result.get("coverage_delta", 0.0),
                    ).to_dict(),
                )
            elif action == ActionType.REVIEW:
                agent_reports = result.get("agent_reports", [])
                item_id = result.get("item_id") or self._last_item_id or ""
                # ISSUE-SAAS-015: Map client status values to server API contract
                # Client uses: complete, timeout, error (execution state)
                # Server expects: pass, fail, warning (quality assessment)
                status_mapping = {
                    "complete": "pass",  # Completed successfully = pass
                    "timeout": "warning",  # Timed out = warning (couldn't complete)
                    "error": "fail",  # Error = fail
                }
                mapped_reports = []
                for report in agent_reports:
                    mapped_report = dict(report)  # Shallow copy
                    client_status = mapped_report.get("status", "complete")
                    mapped_report["status"] = status_mapping.get(client_status, client_status)
                    mapped_reports.append(mapped_report)
                response = self._client._request(
                    "POST",
                    "report_review",
                    json={
                        "session_id": self._session_id,
                        "item_id": item_id,
                        "agent_reports": mapped_reports,
                        "iteration": result.get("iteration", 0),
                    },
                )
            elif action == ActionType.FIX:
                fix_results = result.get("fix_results", [])
                item_id = result.get("item_id") or self._last_item_id or ""
                response = self._client._request(
                    "POST",
                    "report_fix",
                    json={
                        "session_id": self._session_id,
                        "item_id": item_id,  # ISSUE-SAAS-021: Include for fix-review loop
                        "fixes_applied": result.get("fixed_count", 0),
                        "fixes_failed": result.get("failed_count", 0),
                        "fix_details": [
                            {
                                "issue_id": fr.get("issue_id", ""),
                                "status": fr.get("status", ""),
                                "summary": fr.get("summary", ""),  # BUG-SCHEMA-002: Get from fix result, not verification
                            }
                            for fr in fix_results
                        ],
                    },
                )
            elif action == ActionType.ESCALATE:
                response = self._client._request(
                    "POST",
                    "user_decision",
                    json=UserDecision(
                        session_id=self._session_id,
                        escalation_id=result.get("escalation_id", ""),
                        decision=UserDecisionChoice(result.get("decision", "force_complete")),
                        reason=result.get("reason", ""),
                    ).to_dict(),
                )
            else:
                raise OrchestratorError(
                    f"Cannot report result for action: {action.value}",
                    session_id=self._session_id,
                )

            return ServerAction.from_dict(response)

        except APIError:
            raise
        except Exception as e:
            raise OrchestratorError(
                f"Failed to report result: {e}",
                session_id=self._session_id,
            )

    def derive(
        self,
        objective: str,
        working_dir: Path | None = None,
        project_id: str | None = None,
        repo_root: str | None = None,
        llm_provider: str = "anthropic",
        max_iterations: int | None = None,
        plan_id: str | None = None,
        plan_only: bool = False,
    ) -> CompletionNotice:
        """Start a new derivation session.

        This is the main entry point for the hybrid orchestration loop.
        It creates a new session, derives a plan, refines it, executes
        the plan items, runs quality review, and completes the session.

        Args:
            objective: Task objective to plan and execute
            working_dir: Working directory (overrides instance default)
            project_id: Optional project ID override
            repo_root: Optional git repo root (absolute path)
            llm_provider: LLM provider to use
            max_iterations: Maximum orchestration loop iterations (None = use config)
            plan_id: Optional reference to uploaded plan (for plan import workflow)
            plan_only: If True, stop before execution once plan is ready (default: False)

        Returns:
            CompletionNotice with session summary

        Raises:
            ConnectionError: If server is not reachable
            OrchestratorError: If orchestration fails
        """
        # Resolve max_iterations from config if not provided
        if max_iterations is None:
            max_iterations = get_max_iterations()

        # Update working dir if provided
        if working_dir:
            self._working_dir = working_dir

        # Ensure we can reach the server
        self._ensure_online()

        # Gather project context
        project_context = self._get_project_context()
        project_hash = self._hash_working_dir()

        # Get client version
        try:
            from obra import __version__ as client_version
        except ImportError:
            client_version = "0.0.0-dev"

        # Start session
        print_info(f"Starting session for: {objective[:50]}...")
        logger.info(f"Starting session: {objective}")

        # Extract LLM config from stored _llm_config (ISSUE-CLI-005 fix)
        impl_provider = None
        impl_model = None
        thinking_level = None
        if hasattr(self, "_llm_config") and self._llm_config:
            impl_provider = self._llm_config.get("provider")
            impl_model = self._llm_config.get("model")
            thinking_level = self._llm_config.get("thinking_level")
            # Use provider from _llm_config if available
            if self._llm_config.get("provider"):
                llm_provider = self._llm_config.get("provider")

        try:
            response = self._client._request(
                "POST",
                "hybrid_orchestrate",
                json=SessionStart(
                    objective=objective,
                    project_hash=project_hash,
                    project_id=project_id,
                    working_dir=str(self._working_dir),
                    repo_root=repo_root,
                    project_context=project_context,
                    client_version=client_version,
                    llm_provider=llm_provider,
                    impl_provider=impl_provider,
                    impl_model=impl_model,
                    thinking_level=thinking_level,
                    plan_id=plan_id,
                ).to_dict(),
            )
        except APIError as e:
            raise OrchestratorError(
                f"Failed to start session: {e}",
                recovery="Check your authentication with 'obra whoami'",
            )

        # Parse server response
        server_action = ServerAction.from_dict(response)
        self._session_id = server_action.session_id

        resolved_llm = self._apply_resolved_llm_config(server_action.metadata)
        if resolved_llm:
            provider = resolved_llm.get("provider", "unknown")
            model = resolved_llm.get("model", "default")
            thinking = resolved_llm.get("thinking_level", "medium")
            console.print(f"[dim]LLM (server): {provider} ({model}) | thinking: {thinking}[/dim]")

        project_notice = server_action.metadata.get("project_notice")
        if project_notice:
            print_info(project_notice)
        project_warning = server_action.metadata.get("project_warning")
        if project_warning:
            print_warning(project_warning)

        if server_action.is_error():
            raise OrchestratorError(
                server_action.error_message or "Failed to start session",
                session_id=self._session_id,
            )

        # Display bypass mode warnings
        if server_action.bypass_modes_active:
            print_warning(f"Bypass modes active: {', '.join(server_action.bypass_modes_active)}")
            console.print("  Results may not reflect production behavior.")

        logger.info(f"Session started: {self._session_id}")
        print_info(f"Session: {self._session_id[:8]}...")

        # ISSUE-OBS-002: Log session_started event for observability
        self._log_session_event(
            "session_started",
            objective=objective,
            working_dir=str(self._working_dir),
            llm_provider=llm_provider,
            plan_id=plan_id,
            client_version=client_version,
        )

        # Main orchestration loop
        iteration = 0
        poll_count = 0  # Track consecutive WAIT responses for backoff
        while iteration < max_iterations:
            iteration += 1
            logger.debug(f"Orchestration loop iteration {iteration}")

            # Handle current action
            result = self._handle_action(server_action)

            # Check for completion
            if result.get("completed"):
                notice = result.get("notice")
                if isinstance(notice, CompletionNotice):
                    logger.info(f"Session completed: {self._session_id}")
                    # ISSUE-OBS-002: Log session_completed event
                    self._log_session_event(
                        "session_completed",
                        items_completed=notice.items_completed,
                        total_iterations=notice.total_iterations,
                        quality_score=notice.quality_score,
                    )
                    return notice
                # Create notice from result if not already
                notice = CompletionNotice(
                    session_summary=result.get("session_summary", ""),
                    items_completed=result.get("items_completed", 0),
                    total_iterations=result.get("total_iterations", iteration),
                    quality_score=result.get("quality_score", 0.0),
                )
                # ISSUE-OBS-002: Log session_completed event for alternate completion path
                self._log_session_event(
                    "session_completed",
                    items_completed=notice.items_completed,
                    total_iterations=notice.total_iterations,
                    quality_score=notice.quality_score,
                )
                return notice

            # Check for waiting (async processing)
            if result.get("waiting"):
                self._poll_with_backoff(poll_count)
                poll_count += 1
                # Poll server for updated action
                try:
                    response = self._client._request(
                        "GET",
                        f"session/{self._session_id}/action",
                    )
                    server_action = ServerAction.from_dict(response)
                    # Reset failure count on successful poll
                    self._polling_failure_count = 0
                except APIError as e:
                    # Increment failure counter
                    self._polling_failure_count += 1

                    # Log warning on each failure
                    logger.warning(
                        f"Polling backoff exception (attempt {self._polling_failure_count}): {e}"
                    )

                    # After 5 consecutive failures, log error with diagnostics
                    if self._polling_failure_count >= 5:
                        logger.error(
                            f"Polling endpoint failed {self._polling_failure_count} consecutive times. "
                            f"Session: {self._session_id}, "
                            f"Poll count: {poll_count}, "
                            f"Iteration: {iteration}, "
                            f"Last error: {e}"
                        )

                    # Continue with current action if polling endpoint not available
                continue
            # Reset poll count when not waiting
            poll_count = 0

            # Report result and get next action
            report_as = result.pop("_report_as", None)
            action_to_report = (
                ActionType(report_as) if isinstance(report_as, str) and report_as else server_action.action
            )
            server_action = self._report_result(action_to_report, result)

            # Plan-only mode: stop before execution once plan is ready.
            if plan_only and server_action.action in (ActionType.EXECUTE, ActionType.REVIEW, ActionType.FIX):
                if action_to_report == ActionType.REVISE:
                    plan_summary = result.get("changes_summary", "Plan revised")
                    items_count = len(result.get("plan_items", []))
                elif action_to_report == ActionType.EXAMINE:
                    issues_count = len(result.get("issues", []))
                    plan_summary = f"Plan examined with {issues_count} issue(s)"
                    items_count = 0
                else:
                    plan_summary = "Plan-only mode: stopping before execution"
                    items_count = len(result.get("plan_items", []))

                notice = CompletionNotice(
                    session_summary=f"Plan-only mode: {plan_summary}",
                    items_completed=0,
                    total_iterations=iteration,
                    quality_score=0.0,
                )

                logger.info(f"Plan-only session completed: {self._session_id}")
                self._log_session_event(
                    "session_completed",
                    plan_only=True,
                    plan_items_count=items_count,
                    total_iterations=iteration,
                )
                return notice

            # Check for error response
            if server_action.is_error():
                raise OrchestratorError(
                    server_action.error_message or "Server returned error",
                    session_id=self._session_id,
                )

        # Max iterations reached
        raise OrchestratorError(
            f"Orchestration loop exceeded {max_iterations} iterations",
            session_id=self._session_id,
            recovery=f"This may indicate a bug. Resume with: obra resume --session-id {self._session_id}",
        )

    def resume(self, session_id: str) -> CompletionNotice:
        """Resume an interrupted session.

        Args:
            session_id: Session ID to resume

        Returns:
            CompletionNotice with session summary

        Raises:
            ConnectionError: If server is not reachable
            OrchestratorError: If session cannot be resumed
        """
        self._ensure_online()

        # Get session state
        try:
            response = self._client.get_session(session_id)
            resume_context = ResumeContext.from_dict(response)
        except APIError as e:
            if e.status_code == 404:
                raise OrchestratorError(
                    f"Session not found: {session_id}",
                    recovery="The session may have expired. Start a new session with 'obra derive'",
                )
            raise

        if not resume_context.can_resume:
            raise OrchestratorError(
                f"Session cannot be resumed: {resume_context.pending_action}",
                session_id=session_id,
            )

        self._session_id = session_id
        print_info(f"Resuming session: {session_id[:8]}...")
        print_info(f"  Last step: {resume_context.last_successful_step}")

        # Request resume from server
        try:
            response = self._client._request(
                "POST",
                "resume",
                json={"session_id": session_id},
            )
        except APIError as e:
            raise OrchestratorError(
                f"Failed to resume session: {e}",
                session_id=session_id,
            )

        server_action = ServerAction.from_dict(response)

        # Continue orchestration loop from resume point
        iteration = 0
        poll_count = 0  # Track consecutive WAIT responses for backoff
        max_iterations = get_max_iterations()
        while iteration < max_iterations:
            iteration += 1

            result = self._handle_action(server_action)

            if result.get("completed"):
                notice = result.get("notice")
                if isinstance(notice, CompletionNotice):
                    return notice
                return CompletionNotice(
                    session_summary=result.get("session_summary", ""),
                    items_completed=result.get("items_completed", 0),
                    total_iterations=result.get("total_iterations", iteration),
                    quality_score=result.get("quality_score", 0.0),
                )

            if result.get("waiting"):
                self._poll_with_backoff(poll_count)
                poll_count += 1
                # Poll server for updated action
                try:
                    response = self._client._request(
                        "GET",
                        f"session/{self._session_id}/action",
                    )
                    server_action = ServerAction.from_dict(response)
                except APIError:
                    # If polling endpoint not available, continue with current action
                    pass
                continue
            # Reset poll count when not waiting
            poll_count = 0

            server_action = self._report_result(server_action.action, result)

            if server_action.is_error():
                raise OrchestratorError(
                    server_action.error_message or "Server returned error",
                    session_id=self._session_id,
                )

        raise OrchestratorError(
            f"Orchestration loop exceeded {max_iterations} iterations",
            session_id=self._session_id,
        )

    def get_status(self, session_id: str | None = None) -> ResumeContext:
        """Get session status.

        Args:
            session_id: Session ID to check (defaults to current session)

        Returns:
            ResumeContext with session status

        Raises:
            OrchestratorError: If no session ID provided and no active session
        """
        sid = session_id or self._session_id
        if not sid:
            raise OrchestratorError(
                "No session ID provided",
                recovery="Provide a session ID or start a new session with 'obra derive'",
            )

        try:
            response = self._client._request("GET", f"session/{sid}")
            return ResumeContext.from_dict(response)
        except APIError as e:
            if e.status_code == 404:
                raise OrchestratorError(
                    f"Session not found: {sid}",
                    recovery="The session may have expired.",
                )
            raise


__all__ = [
    "ConnectionError",
    "HybridOrchestrator",
    "OrchestratorError",
]
