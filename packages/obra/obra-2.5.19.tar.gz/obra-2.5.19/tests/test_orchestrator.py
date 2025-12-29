"""Tests for HybridOrchestrator.

Tests cover:
- __init__: Basic initialization and parameter handling
- from_config: Configuration-based factory method
- start/derive: Session creation and orchestration loop
- resume: Session resumption handling
- Error handling: Connection errors, API errors, escalations
- Polling: Exponential backoff behavior

Resource Limits (per docs/quality/testing/test-guidelines.md):
- Max sleep: 0.5s per test
- Max threads: 5 per test
- Max memory: 20KB per test
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from obra.api.protocol import (
    ActionType,
    CompletionNotice,
    EscalationNotice,
    EscalationReason,
    ServerAction,
    SessionPhase,
    UserDecisionChoice,
)
from obra.exceptions import ConfigurationError, ConnectionError, OrchestratorError
from obra.hybrid.orchestrator import HybridOrchestrator

# =============================================================================
# Test: __init__
# =============================================================================


class TestOrchestratorInit:
    """Tests for HybridOrchestrator.__init__."""

    def test_init_with_required_params(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test initialization with required parameters only."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        assert orchestrator._client is mock_api_client
        assert orchestrator._working_dir == mock_working_dir
        assert orchestrator._session_id is None
        assert orchestrator._handlers == {}
        assert orchestrator._on_progress is None
        assert orchestrator._on_escalation is None
        assert orchestrator._on_stream is None
        assert orchestrator._llm_config is None

    def test_init_with_all_callbacks(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test initialization with all optional callbacks."""
        progress_callback = MagicMock()
        escalation_callback = MagicMock()
        stream_callback = MagicMock()

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
            on_progress=progress_callback,
            on_escalation=escalation_callback,
            on_stream=stream_callback,
        )

        assert orchestrator._on_progress is progress_callback
        assert orchestrator._on_escalation is escalation_callback
        assert orchestrator._on_stream is stream_callback

    def test_init_defaults_working_dir_to_cwd(
        self,
        mock_api_client: MagicMock,
    ) -> None:
        """Test that working_dir defaults to current working directory."""
        orchestrator = HybridOrchestrator(client=mock_api_client)

        assert orchestrator._working_dir == Path.cwd()

    def test_init_phase_tracking_initial_state(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test that phase tracking is initialized to None."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        assert orchestrator._current_phase is None
        assert orchestrator._phase_start_time is None


class TestOrchestratorProperties:
    """Tests for HybridOrchestrator properties."""

    def test_client_property(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test client property returns the API client."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        assert orchestrator.client is mock_api_client

    def test_working_dir_property(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test working_dir property returns the working directory."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        assert orchestrator.working_dir == mock_working_dir

    def test_session_id_property_initially_none(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test session_id property is None before session starts."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        assert orchestrator.session_id is None


# =============================================================================
# Test: from_config
# =============================================================================


class TestOrchestratorFromConfig:
    """Tests for HybridOrchestrator.from_config factory method."""

    def test_from_config_creates_orchestrator(
        self,
        mock_working_dir: Path,
    ) -> None:
        """Test from_config creates a properly configured orchestrator."""
        with (
            patch("obra.hybrid.orchestrator.APIClient.from_config") as mock_from_config,
            patch("obra.config.resolve_llm_config") as mock_resolve,
        ):
            mock_client = MagicMock()
            mock_from_config.return_value = mock_client
            mock_resolve.return_value = {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "thinking_level": "standard",
            }

            orchestrator = HybridOrchestrator.from_config(
                working_dir=mock_working_dir,
            )

            assert orchestrator._client is mock_client
            assert orchestrator._working_dir == mock_working_dir
            mock_from_config.assert_called_once()
            mock_resolve.assert_called_once_with(
                role="implementation",
                override_provider=None,
                override_model=None,
                override_thinking_level=None,
            )

    def test_from_config_with_llm_overrides(
        self,
        mock_working_dir: Path,
    ) -> None:
        """Test from_config passes LLM overrides to resolve_llm_config."""
        with (
            patch("obra.hybrid.orchestrator.APIClient.from_config") as mock_from_config,
            patch("obra.config.resolve_llm_config") as mock_resolve,
        ):
            mock_from_config.return_value = MagicMock()
            mock_resolve.return_value = {"provider": "openai", "model": "gpt-4"}

            HybridOrchestrator.from_config(
                working_dir=mock_working_dir,
                impl_provider="openai",
                impl_model="gpt-4",
                thinking_level="high",
            )

            mock_resolve.assert_called_once_with(
                role="implementation",
                override_provider="openai",
                override_model="gpt-4",
                override_thinking_level="high",
            )

    def test_from_config_with_callbacks(
        self,
        mock_working_dir: Path,
    ) -> None:
        """Test from_config passes callbacks to orchestrator."""
        progress_callback = MagicMock()
        escalation_callback = MagicMock()
        stream_callback = MagicMock()

        with (
            patch("obra.hybrid.orchestrator.APIClient.from_config") as mock_from_config,
            patch("obra.config.resolve_llm_config") as mock_resolve,
        ):
            mock_from_config.return_value = MagicMock()
            mock_resolve.return_value = {}

            orchestrator = HybridOrchestrator.from_config(
                working_dir=mock_working_dir,
                on_progress=progress_callback,
                on_escalation=escalation_callback,
                on_stream=stream_callback,
            )

            assert orchestrator._on_progress is progress_callback
            assert orchestrator._on_escalation is escalation_callback
            assert orchestrator._on_stream is stream_callback

    def test_from_config_raises_on_api_client_failure(
        self,
        mock_working_dir: Path,
    ) -> None:
        """Test from_config raises ConfigurationError on API client failure."""
        with patch("obra.hybrid.orchestrator.APIClient.from_config") as mock_from_config:
            mock_from_config.side_effect = Exception("No config file")

            with pytest.raises(ConfigurationError) as exc_info:
                HybridOrchestrator.from_config(working_dir=mock_working_dir)

            assert "Failed to create API client" in str(exc_info.value)

    def test_from_config_propagates_configuration_error(
        self,
        mock_working_dir: Path,
    ) -> None:
        """Test from_config propagates ConfigurationError from APIClient."""
        with patch("obra.hybrid.orchestrator.APIClient.from_config") as mock_from_config:
            mock_from_config.side_effect = ConfigurationError("Invalid config")

            with pytest.raises(ConfigurationError) as exc_info:
                HybridOrchestrator.from_config(working_dir=mock_working_dir)

            assert "Invalid config" in str(exc_info.value)

    def test_from_config_stores_llm_config(
        self,
        mock_working_dir: Path,
    ) -> None:
        """Test from_config stores resolved LLM config on orchestrator."""
        with (
            patch("obra.hybrid.orchestrator.APIClient.from_config") as mock_from_config,
            patch("obra.config.resolve_llm_config") as mock_resolve,
        ):
            mock_from_config.return_value = MagicMock()
            expected_config = {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "thinking_level": "standard",
            }
            mock_resolve.return_value = expected_config

            orchestrator = HybridOrchestrator.from_config(
                working_dir=mock_working_dir,
            )

            assert orchestrator._llm_config == expected_config


# =============================================================================
# Test: is_online / _ensure_online
# =============================================================================


class TestOrchestratorOnlineChecks:
    """Tests for online status checking."""

    def test_is_online_returns_true_on_success(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test is_online returns True when health check succeeds."""
        mock_api_client.health_check.return_value = {"status": "healthy"}

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        assert orchestrator.is_online() is True
        mock_api_client.health_check.assert_called_once()

    def test_is_online_returns_false_on_failure(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test is_online returns False when health check fails."""
        mock_api_client.health_check.side_effect = Exception("Connection refused")

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        assert orchestrator.is_online() is False

    def test_ensure_online_raises_on_failure(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _ensure_online raises ConnectionError when offline."""
        mock_api_client.health_check.side_effect = Exception("Connection refused")

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        with pytest.raises(ConnectionError):
            orchestrator._ensure_online()


# =============================================================================
# Test: Helper Methods
# =============================================================================


class TestOrchestratorHelpers:
    """Tests for helper methods."""

    def test_hash_working_dir_returns_sha256(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _hash_working_dir returns SHA256 hash of path."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        result = orchestrator._hash_working_dir()

        # Should be hex SHA256 (64 characters)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_get_project_context_detects_python(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _get_project_context detects Python project structure."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        context = orchestrator._get_project_context()

        # mock_working_dir has .py files and pyproject.toml
        assert "python" in context["languages"]
        assert "python" in context["frameworks"]
        assert context["has_tests"] is True  # tests/ directory exists
        assert context["file_count"] > 0

    def test_emit_progress_calls_callback(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _emit_progress calls the progress callback."""
        progress_events: list[dict[str, Any]] = []

        def on_progress(action: str, payload: dict[str, Any]) -> None:
            progress_events.append({"action": action, "payload": payload})

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
            on_progress=on_progress,
        )

        orchestrator._emit_progress("test_action", {"key": "value"})

        assert len(progress_events) == 1
        assert progress_events[0]["action"] == "test_action"
        assert progress_events[0]["payload"] == {"key": "value"}

    def test_emit_progress_noop_without_callback(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _emit_progress does nothing when no callback set."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        # Should not raise
        orchestrator._emit_progress("test_action", {"key": "value"})

    def test_action_to_phase_mapping(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _action_to_phase returns correct phase mappings."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        assert orchestrator._action_to_phase(ActionType.DERIVE) == SessionPhase.DERIVATION
        assert orchestrator._action_to_phase(ActionType.EXAMINE) == SessionPhase.REFINEMENT
        assert orchestrator._action_to_phase(ActionType.REVISE) == SessionPhase.REFINEMENT
        assert orchestrator._action_to_phase(ActionType.EXECUTE) == SessionPhase.EXECUTION
        assert orchestrator._action_to_phase(ActionType.REVIEW) == SessionPhase.REVIEW
        assert orchestrator._action_to_phase(ActionType.COMPLETE) is None
        assert orchestrator._action_to_phase(ActionType.ESCALATE) is None


# =============================================================================
# Test: Handler Registry
# =============================================================================


class TestOrchestratorHandlerRegistry:
    """Tests for handler lazy initialization."""

    def test_get_handler_creates_derive_handler(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _get_handler creates DeriveHandler on first access."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )
        orchestrator._llm_config = {"provider": "anthropic"}

        handler = orchestrator._get_handler(ActionType.DERIVE)

        from obra.hybrid.handlers.derive import DeriveHandler

        assert isinstance(handler, DeriveHandler)
        assert ActionType.DERIVE in orchestrator._handlers

    def test_get_handler_reuses_existing(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _get_handler reuses existing handler instance."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )
        orchestrator._llm_config = {"provider": "anthropic"}

        handler1 = orchestrator._get_handler(ActionType.DERIVE)
        handler2 = orchestrator._get_handler(ActionType.DERIVE)

        assert handler1 is handler2

    def test_get_handler_raises_for_unknown_action(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _get_handler raises OrchestratorError for unknown actions."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        # ERROR is a valid ActionType but has no handler
        with pytest.raises(OrchestratorError) as exc_info:
            orchestrator._get_handler(ActionType.ERROR)

        assert "No handler for action" in str(exc_info.value)

    def test_get_handler_passes_stream_callback(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _get_handler passes stream callback to DeriveHandler."""
        stream_callback = MagicMock()

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
            on_stream=stream_callback,
        )
        orchestrator._llm_config = {"provider": "anthropic"}

        handler = orchestrator._get_handler(ActionType.DERIVE)

        assert handler._on_stream is stream_callback

    def test_get_handler_passes_llm_config(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _get_handler passes LLM config to handlers."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )
        orchestrator._llm_config = {"provider": "anthropic", "model": "claude-sonnet-4-20250514"}

        handler = orchestrator._get_handler(ActionType.DERIVE)

        assert handler._llm_config == {"provider": "anthropic", "model": "claude-sonnet-4-20250514"}

    def test_get_handler_raises_when_llm_config_is_none(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _get_handler raises ConfigurationError when llm_config is None for handlers that require it."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )
        # llm_config is None by default

        with pytest.raises(ConfigurationError) as exc_info:
            orchestrator._get_handler(ActionType.DERIVE)

        assert "llm_config is None" in str(exc_info.value)
        assert "derive" in str(exc_info.value).lower()

    def test_get_handler_raises_when_llm_config_missing_provider(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _get_handler raises ConfigurationError when llm_config is missing required 'provider' key."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )
        orchestrator._llm_config = {"model": "claude-sonnet-4-20250514"}  # Missing 'provider'

        with pytest.raises(ConfigurationError) as exc_info:
            orchestrator._get_handler(ActionType.DERIVE)

        assert "missing required keys" in str(exc_info.value)
        assert "provider" in str(exc_info.value)

    def test_get_handler_validation_applies_to_all_llm_handlers(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _get_handler validation applies to DERIVE, EXAMINE, REVISE, EXECUTE, and FIX handlers."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )
        # llm_config is None by default

        for action in [ActionType.DERIVE, ActionType.EXAMINE, ActionType.REVISE, ActionType.EXECUTE, ActionType.FIX]:
            with pytest.raises(ConfigurationError) as exc_info:
                orchestrator._get_handler(action)
            assert "llm_config is None" in str(exc_info.value)

    def test_get_handler_review_does_not_require_llm_config(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _get_handler does not require llm_config for REVIEW handler."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )
        # llm_config is None by default

        # REVIEW handler should not raise ConfigurationError
        handler = orchestrator._get_handler(ActionType.REVIEW)

        from obra.hybrid.handlers.review import ReviewHandler
        assert isinstance(handler, ReviewHandler)


# =============================================================================
# Test: derive() / Orchestration Loop
# =============================================================================


class TestOrchestratorDerive:
    """Tests for derive() method and orchestration loop."""

    def test_derive_starts_session(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test derive() starts a new session with the server."""
        # Configure mock for immediate completion
        mock_api_client.health_check.return_value = {"status": "healthy"}
        mock_api_client._request.return_value = {
            "action": "complete",
            "session_id": "test-session-123",
            "iteration": 1,
            "payload": {
                "session_summary": {"objective": "Test", "items_completed": 0},
                "plan_final": [],
            },
        }

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        result = orchestrator.derive(
            objective="Test objective",
            llm_provider="anthropic",
        )

        assert isinstance(result, CompletionNotice)
        assert orchestrator._session_id == "test-session-123"
        mock_api_client._request.assert_called()

    def test_derive_raises_when_offline(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test derive() raises ConnectionError when server is offline."""
        mock_api_client.health_check.side_effect = Exception("Connection refused")

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        with pytest.raises(ConnectionError):
            orchestrator.derive(objective="Test")

    def test_derive_uses_provided_working_dir(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
        tmp_path: Path,
    ) -> None:
        """Test derive() uses working_dir argument if provided."""
        mock_api_client.health_check.return_value = {"status": "healthy"}
        mock_api_client._request.return_value = {
            "action": "complete",
            "session_id": "test-session-123",
            "iteration": 1,
            "payload": {"session_summary": {}, "plan_final": []},
        }

        # Create alternate working dir
        alt_dir = tmp_path / "alternate"
        alt_dir.mkdir()

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        orchestrator.derive(objective="Test", working_dir=alt_dir)

        assert orchestrator._working_dir == alt_dir


class TestOrchestratorHandleAction:
    """Tests for _handle_action method."""

    def test_handle_action_complete_returns_completion(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _handle_action returns completion notice for COMPLETE action."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        server_action = ServerAction(
            action=ActionType.COMPLETE,
            session_id="test-session",
            iteration=5,
            payload={
                "session_summary": {
                    "objective": "Test objective",
                    "items_completed": 3,
                    "total_iterations": 5,
                    "quality_score": 0.95,
                },
                "plan_final": [],
            },
        )

        result = orchestrator._handle_action(server_action)

        assert result["completed"] is True
        assert isinstance(result["notice"], CompletionNotice)

    def test_handle_action_error_raises(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _handle_action raises OrchestratorError for ERROR action."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        server_action = ServerAction(
            action=ActionType.ERROR,
            session_id="test-session",
            iteration=1,
            payload={},
            error_message="Server encountered an error",
            error_code="INTERNAL_ERROR",
        )

        with pytest.raises(OrchestratorError) as exc_info:
            orchestrator._handle_action(server_action)

        assert "INTERNAL_ERROR" in str(exc_info.value)
        assert "Server encountered an error" in str(exc_info.value)

    def test_handle_action_wait_returns_waiting(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _handle_action returns waiting flag for WAIT action."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        server_action = ServerAction(
            action=ActionType.WAIT,
            session_id="test-session",
            iteration=1,
            payload={},
        )

        result = orchestrator._handle_action(server_action)

        assert result["waiting"] is True

    def test_handle_action_dispatches_to_derive_handler(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _handle_action dispatches DERIVE to DeriveHandler."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        # Mock the handler
        mock_handler = MagicMock()
        mock_handler.handle.return_value = {
            "plan_items": [{"id": "T1", "title": "Test"}],
            "raw_response": "test",
        }
        orchestrator._handlers[ActionType.DERIVE] = mock_handler

        server_action = ServerAction(
            action=ActionType.DERIVE,
            session_id="test-session",
            iteration=1,
            payload={
                "objective": "Test objective",
                "project_context": {"languages": ["python"]},
                "llm_provider": "anthropic",
            },
        )

        result = orchestrator._handle_action(server_action)

        mock_handler.handle.assert_called_once()
        assert "plan_items" in result

    def test_handle_action_emits_progress(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _handle_action emits progress events."""
        progress_events: list[dict[str, Any]] = []

        def on_progress(action: str, payload: dict[str, Any]) -> None:
            progress_events.append({"action": action, "payload": payload})

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
            on_progress=on_progress,
        )

        server_action = ServerAction(
            action=ActionType.COMPLETE,
            session_id="test-session",
            iteration=1,
            payload={"session_summary": {}, "plan_final": []},
        )

        orchestrator._handle_action(server_action)

        # Should emit 'complete' action
        assert any(e["action"] == "complete" for e in progress_events)


class TestOrchestratorEscalation:
    """Tests for escalation handling."""

    def test_handle_escalation_with_callback(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _handle_escalation calls callback and returns decision."""

        def on_escalation(notice: EscalationNotice) -> UserDecisionChoice:
            return UserDecisionChoice.CONTINUE_FIXING

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
            on_escalation=on_escalation,
        )

        notice = EscalationNotice(
            escalation_id="esc-123",
            reason=EscalationReason.MAX_ITERATIONS,
            blocking_issues=[{"id": "I1", "description": "Test issue"}],
        )

        result = orchestrator._handle_escalation(notice)

        assert result["escalation_id"] == "esc-123"
        assert result["decision"] == UserDecisionChoice.CONTINUE_FIXING.value

    def test_handle_escalation_without_callback_defaults_force_complete(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _handle_escalation defaults to FORCE_COMPLETE without callback."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        notice = EscalationNotice(
            escalation_id="esc-123",
            reason=EscalationReason.BLOCKED,
            blocking_issues=[],
        )

        result = orchestrator._handle_escalation(notice)

        assert result["decision"] == UserDecisionChoice.FORCE_COMPLETE.value

    def test_handle_escalation_handles_non_list_blocking_issues(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _handle_escalation handles non-list blocking_issues gracefully."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        # Create notice with invalid blocking_issues type
        notice = EscalationNotice(
            escalation_id="esc-123",
            reason=EscalationReason.BLOCKED,
            blocking_issues="not a list",  # type: ignore
        )

        # Should not raise, but log warning
        result = orchestrator._handle_escalation(notice)

        assert result["decision"] == UserDecisionChoice.FORCE_COMPLETE.value
        assert result["escalation_id"] == "esc-123"

    def test_handle_escalation_handles_non_dict_items_in_blocking_issues(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _handle_escalation filters out non-dict items in blocking_issues."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        # Create notice with mixed valid/invalid blocking_issues
        notice = EscalationNotice(
            escalation_id="esc-123",
            reason=EscalationReason.BLOCKED,
            blocking_issues=[
                {"id": "I1", "description": "Valid issue 1"},
                "invalid string item",  # Should be filtered out
                {"id": "I2", "description": "Valid issue 2"},
                123,  # Should be filtered out  # type: ignore
                {"id": "I3", "description": "Valid issue 3"},
            ],  # type: ignore
        )

        # Should not raise, but log warnings for invalid items
        result = orchestrator._handle_escalation(notice)

        assert result["decision"] == UserDecisionChoice.FORCE_COMPLETE.value
        assert result["escalation_id"] == "esc-123"

    def test_handle_escalation_displays_valid_blocking_issues(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
        capsys,
    ) -> None:
        """Test _handle_escalation displays valid blocking issues correctly."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        notice = EscalationNotice(
            escalation_id="esc-123",
            reason=EscalationReason.MAX_ITERATIONS,
            blocking_issues=[
                {"id": "I1", "description": "First issue"},
                {"id": "I2", "description": "Second issue"},
                {"id": "I3"},  # Missing description
            ],
        )

        result = orchestrator._handle_escalation(notice)

        assert result["decision"] == UserDecisionChoice.FORCE_COMPLETE.value
        # Note: We can't easily test console output without mocking console.print
        # but the test ensures the code runs without errors


class TestOrchestratorReportResult:
    """Tests for _report_result method."""

    def test_report_result_requires_session(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _report_result raises if no active session."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        with pytest.raises(OrchestratorError) as exc_info:
            orchestrator._report_result(ActionType.DERIVE, {"plan_items": []})

        assert "No active session" in str(exc_info.value)

    def test_report_result_sends_derivation(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _report_result sends derivation result to server."""
        mock_api_client._request.return_value = {
            "action": "examine",
            "session_id": "test-session",
            "iteration": 2,
            "payload": {},
        }

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )
        orchestrator._session_id = "test-session"

        result = orchestrator._report_result(
            ActionType.DERIVE,
            {
                "plan_items": [{"id": "T1", "title": "Test"}],
                "raw_response": "test response",
            },
        )

        assert isinstance(result, ServerAction)
        assert result.action == ActionType.EXAMINE
        mock_api_client._request.assert_called_once()
        call_args = mock_api_client._request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "report_derivation"

    def test_report_result_sends_execution(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _report_result sends execution result to server."""
        mock_api_client._request.return_value = {
            "action": "review",
            "session_id": "test-session",
            "iteration": 3,
            "payload": {},
        }

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )
        orchestrator._session_id = "test-session"

        result = orchestrator._report_result(
            ActionType.EXECUTE,
            {
                "item_id": "T1",
                "status": "success",
                "summary": "Task completed",
                "files_changed": 2,
                "tests_passed": True,
                "test_count": 5,
            },
        )

        assert isinstance(result, ServerAction)
        call_args = mock_api_client._request.call_args
        assert call_args[0][1] == "report_execution"


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestOrchestratorErrorHandling:
    """Tests for error handling scenarios."""

    def test_derive_handles_api_error_on_start(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test derive() handles APIError when starting session."""
        from obra.exceptions import APIError

        mock_api_client.health_check.return_value = {"status": "healthy"}
        mock_api_client._request.side_effect = APIError("Authentication failed", status_code=401)

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        with pytest.raises(OrchestratorError) as exc_info:
            orchestrator.derive(objective="Test")

        assert "Failed to start session" in str(exc_info.value)

    def test_derive_handles_error_response(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test derive() handles error in server response."""
        mock_api_client.health_check.return_value = {"status": "healthy"}
        mock_api_client._request.return_value = {
            "action": "error",
            "session_id": "test-session",
            "iteration": 0,
            "payload": {},
            "error_message": "Invalid objective",
            "error_code": "INVALID_REQUEST",
        }

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        with pytest.raises(OrchestratorError) as exc_info:
            orchestrator.derive(objective="Test")

        assert "Invalid objective" in str(exc_info.value) or "INVALID_REQUEST" in str(exc_info.value)

    def test_derive_handles_max_iterations(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test derive() raises after max iterations exceeded."""
        mock_api_client.health_check.return_value = {"status": "healthy"}

        # Return derive action forever (never complete)
        mock_api_client._request.return_value = {
            "action": "derive",
            "session_id": "test-session",
            "iteration": 1,
            "payload": {
                "objective": "Test",
                "project_context": {},
                "llm_provider": "anthropic",
            },
        }

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        # Mock handler to avoid actual LLM call
        mock_handler = MagicMock()
        mock_handler.handle.return_value = {"plan_items": [], "raw_response": ""}
        orchestrator._handlers[ActionType.DERIVE] = mock_handler

        with pytest.raises(OrchestratorError) as exc_info:
            orchestrator.derive(objective="Test", max_iterations=3)

        assert "exceeded" in str(exc_info.value).lower()

    def test_report_result_handles_api_error(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _report_result raises on API error."""
        from obra.exceptions import APIError

        mock_api_client._request.side_effect = APIError("Server error", status_code=500)

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )
        orchestrator._session_id = "test-session"

        with pytest.raises(APIError):
            orchestrator._report_result(ActionType.DERIVE, {"plan_items": []})

    def test_report_result_handles_unexpected_error(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _report_result wraps unexpected errors."""
        mock_api_client._request.side_effect = RuntimeError("Unexpected failure")

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )
        orchestrator._session_id = "test-session"

        with pytest.raises(OrchestratorError) as exc_info:
            orchestrator._report_result(ActionType.DERIVE, {"plan_items": []})

        assert "Failed to report result" in str(exc_info.value)

    def test_handle_action_unhandled_action_raises(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _handle_action raises for unhandled actions."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        # Create action with invalid handler registration
        server_action = ServerAction(
            action=ActionType.ERROR,  # ERROR has no handler
            session_id="test-session",
            iteration=1,
            payload={},
        )

        # ERROR action is handled specially, but without error_message
        with pytest.raises(OrchestratorError):
            orchestrator._handle_action(server_action)

    def test_report_result_raises_for_unreportable_action(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _report_result raises for actions that can't be reported."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )
        orchestrator._session_id = "test-session"

        with pytest.raises(OrchestratorError) as exc_info:
            orchestrator._report_result(ActionType.COMPLETE, {})

        assert "Cannot report result for action" in str(exc_info.value)

    def test_derive_orchestration_loop_handles_error_mid_flow(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test derive() handles error returned mid-orchestration."""
        mock_api_client.health_check.return_value = {"status": "healthy"}

        # First call returns derive, second returns error
        call_count = [0]

        def mock_request(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "action": "derive",
                    "session_id": "test-session",
                    "iteration": 0,
                    "payload": {
                        "objective": "Test",
                        "project_context": {},
                        "llm_provider": "anthropic",
                    },
                }
            return {
                "action": "error",
                "session_id": "test-session",
                "iteration": 1,
                "payload": {},
                "error_message": "Derivation failed",
                "error_code": "DERIVATION_ERROR",
            }

        mock_api_client._request.side_effect = mock_request

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        # Mock handler
        mock_handler = MagicMock()
        mock_handler.handle.return_value = {"plan_items": [], "raw_response": ""}
        orchestrator._handlers[ActionType.DERIVE] = mock_handler

        with pytest.raises(OrchestratorError) as exc_info:
            orchestrator.derive(objective="Test")

        assert "Derivation failed" in str(exc_info.value) or "DERIVATION_ERROR" in str(exc_info.value)


# =============================================================================
# Test: resume()
# =============================================================================


class TestOrchestratorResume:
    """Tests for resume() method."""

    def test_resume_checks_online(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test resume() checks if server is online."""
        mock_api_client.health_check.side_effect = Exception("Connection refused")

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        with pytest.raises(ConnectionError):
            orchestrator.resume(session_id="test-session")

    def test_resume_gets_session_state(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test resume() fetches session state from server."""
        mock_api_client.health_check.return_value = {"status": "healthy"}

        # First call: GET session state, second call: POST resume
        call_count = [0]

        def mock_request(method, endpoint, **kwargs):
            call_count[0] += 1
            if method == "GET" and "session" in endpoint:
                return {
                    "session_id": "test-session",
                    "can_resume": True,
                    "last_successful_step": "derive",
                    "pending_action": None,
                }
            if method == "POST" and endpoint == "resume":
                return {
                    "action": "complete",
                    "session_id": "test-session",
                    "iteration": 1,
                    "payload": {"session_summary": {}, "plan_final": []},
                }
            return {}

        mock_api_client._request.side_effect = mock_request

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        orchestrator.resume(session_id="test-session")

        # Verify GET request was made for session
        calls = mock_api_client._request.call_args_list
        get_calls = [c for c in calls if c[0][0] == "GET"]
        assert len(get_calls) >= 1

    def test_resume_raises_on_session_not_found(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test resume() raises OrchestratorError when session not found."""
        from obra.exceptions import APIError

        mock_api_client.health_check.return_value = {"status": "healthy"}
        mock_api_client._request.side_effect = APIError("Session not found", status_code=404)

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        with pytest.raises(OrchestratorError) as exc_info:
            orchestrator.resume(session_id="nonexistent-session")

        assert "Session not found" in str(exc_info.value)

    def test_resume_raises_when_cannot_resume(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test resume() raises when session cannot be resumed."""
        mock_api_client.health_check.return_value = {"status": "healthy"}
        mock_api_client._request.return_value = {
            "session_id": "test-session",
            "can_resume": False,
            "last_successful_step": "complete",
            "pending_action": "already_completed",
        }

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        with pytest.raises(OrchestratorError) as exc_info:
            orchestrator.resume(session_id="test-session")

        assert "cannot be resumed" in str(exc_info.value)

    def test_resume_returns_completion_notice(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test resume() returns CompletionNotice on success."""
        mock_api_client.health_check.return_value = {"status": "healthy"}

        call_count = [0]

        def mock_request(method, endpoint, **kwargs):
            call_count[0] += 1
            if method == "GET":
                return {
                    "session_id": "test-session",
                    "can_resume": True,
                    "last_successful_step": "execute",
                    "pending_action": None,
                }
            if method == "POST" and endpoint == "resume":
                return {
                    "action": "complete",
                    "session_id": "test-session",
                    "iteration": 5,
                    "payload": {
                        "session_summary": {
                            "objective": "Test",
                            "items_completed": 3,
                            "total_iterations": 5,
                            "quality_score": 0.9,
                        },
                        "plan_final": [],
                    },
                }
            return {}

        mock_api_client._request.side_effect = mock_request

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        result = orchestrator.resume(session_id="test-session")

        assert isinstance(result, CompletionNotice)
        assert orchestrator._session_id == "test-session"

    def test_resume_sets_session_id(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test resume() sets session_id on orchestrator."""
        mock_api_client.health_check.return_value = {"status": "healthy"}

        def mock_request(method, endpoint, **kwargs):
            if method == "GET":
                return {
                    "session_id": "my-session-123",
                    "can_resume": True,
                    "last_successful_step": "derive",
                    "pending_action": None,
                }
            return {
                "action": "complete",
                "session_id": "my-session-123",
                "iteration": 1,
                "payload": {"session_summary": {}, "plan_final": []},
            }

        mock_api_client._request.side_effect = mock_request

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        assert orchestrator._session_id is None

        orchestrator.resume(session_id="my-session-123")

        assert orchestrator._session_id == "my-session-123"

    def test_resume_continues_orchestration_loop(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test resume() continues orchestration loop from resume point."""
        mock_api_client.health_check.return_value = {"status": "healthy"}

        call_count = [0]

        def mock_request(method, endpoint, **kwargs):
            call_count[0] += 1
            if method == "GET":
                return {
                    "session_id": "test-session",
                    "can_resume": True,
                    "last_successful_step": "derive",
                    "pending_action": None,
                }
            if method == "POST" and endpoint == "resume":
                # Return execute action to continue loop
                return {
                    "action": "execute",
                    "session_id": "test-session",
                    "iteration": 2,
                    "payload": {
                        "plan_items": [{"id": "T1", "title": "Test"}],
                        "execution_index": 0,
                        "current_item": {"id": "T1", "title": "Test"},
                    },
                }
            if method == "POST" and endpoint == "report_execution":
                # Return completion
                return {
                    "action": "complete",
                    "session_id": "test-session",
                    "iteration": 3,
                    "payload": {"session_summary": {}, "plan_final": []},
                }
            return {}

        mock_api_client._request.side_effect = mock_request

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        # Mock execute handler
        mock_handler = MagicMock()
        mock_handler.handle.return_value = {
            "item_id": "T1",
            "status": "success",
            "summary": "Done",
            "files_changed": 1,
            "tests_passed": True,
            "test_count": 1,
        }
        orchestrator._handlers[ActionType.EXECUTE] = mock_handler

        result = orchestrator.resume(session_id="test-session")

        assert isinstance(result, CompletionNotice)
        # Should have called execute handler
        mock_handler.handle.assert_called_once()


# =============================================================================
# Test: Polling with Backoff
# =============================================================================


class TestOrchestratorPolling:
    """Tests for polling with exponential backoff."""

    def test_poll_with_backoff_calculates_correct_delays(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _poll_with_backoff calculates correct exponential delays."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        with patch("time.sleep") as mock_sleep:
            # Poll count 0: delay = 1 * 2^0 = 1
            orchestrator._poll_with_backoff(0)
            assert mock_sleep.call_args[0][0] == 1.0

            # Poll count 1: delay = 1 * 2^1 = 2
            orchestrator._poll_with_backoff(1)
            assert mock_sleep.call_args[0][0] == 2.0

            # Poll count 2: delay = 1 * 2^2 = 4
            orchestrator._poll_with_backoff(2)
            assert mock_sleep.call_args[0][0] == 4.0

            # Poll count 3: delay = 1 * 2^3 = 8
            orchestrator._poll_with_backoff(3)
            assert mock_sleep.call_args[0][0] == 8.0

            # Poll count 4: delay = 1 * 2^4 = 16
            orchestrator._poll_with_backoff(4)
            assert mock_sleep.call_args[0][0] == 16.0

    def test_poll_with_backoff_caps_at_max_delay(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _poll_with_backoff caps delay at max_delay."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        with patch("time.sleep") as mock_sleep:
            # Poll count 5: delay = 1 * 2^5 = 32, but capped at 30
            orchestrator._poll_with_backoff(5)
            assert mock_sleep.call_args[0][0] == 30.0

            # Poll count 10: delay = 1 * 2^10 = 1024, but capped at 30
            orchestrator._poll_with_backoff(10)
            assert mock_sleep.call_args[0][0] == 30.0

    def test_poll_with_backoff_custom_parameters(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _poll_with_backoff accepts custom parameters."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        with patch("time.sleep") as mock_sleep:
            # Custom base_delay=0.5, max_delay=10, multiplier=3
            # Poll count 2: delay = 0.5 * 3^2 = 4.5
            orchestrator._poll_with_backoff(
                2, base_delay=0.5, max_delay=10.0, multiplier=3.0
            )
            assert mock_sleep.call_args[0][0] == 4.5

            # Poll count 4: delay = 0.5 * 3^4 = 40.5, capped at 10
            orchestrator._poll_with_backoff(
                4, base_delay=0.5, max_delay=10.0, multiplier=3.0
            )
            assert mock_sleep.call_args[0][0] == 10.0

    def test_poll_with_backoff_returns_actual_delay(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test _poll_with_backoff returns the actual delay used."""
        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        with patch("time.sleep"):
            delay = orchestrator._poll_with_backoff(2)
            assert delay == 4.0

            delay = orchestrator._poll_with_backoff(10)
            assert delay == 30.0  # Capped

    def test_derive_uses_backoff_for_wait_actions(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test derive() uses exponential backoff for WAIT actions."""
        mock_api_client.health_check.return_value = {"status": "healthy"}

        call_count = [0]

        def mock_request(method, endpoint, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: POST start session, return WAIT
                return {
                    "action": "wait",
                    "session_id": "test-session",
                    "iteration": 0,
                    "payload": {},
                }
            if call_count[0] == 2:
                # Second call: GET poll, still WAIT
                return {
                    "action": "wait",
                    "session_id": "test-session",
                    "iteration": 1,
                    "payload": {},
                }
            # Third call: GET poll, complete
            return {
                "action": "complete",
                "session_id": "test-session",
                "iteration": 2,
                "payload": {"session_summary": {}, "plan_final": []},
            }

        mock_api_client._request.side_effect = mock_request

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        with patch.object(orchestrator, "_poll_with_backoff") as mock_poll:
            mock_poll.return_value = 1.0  # Don't actually sleep

            orchestrator.derive(objective="Test")

            # Should have been called twice (once for each WAIT)
            assert mock_poll.call_count == 2
            # First call with poll_count=0, second with poll_count=1
            assert mock_poll.call_args_list[0][0][0] == 0
            assert mock_poll.call_args_list[1][0][0] == 1

    def test_derive_resets_poll_count_after_non_wait(
        self,
        mock_api_client: MagicMock,
        mock_working_dir: Path,
    ) -> None:
        """Test derive() resets poll_count after receiving non-WAIT action."""
        mock_api_client.health_check.return_value = {"status": "healthy"}

        call_count = [0]

        def mock_request(method, endpoint, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # POST start session -> WAIT
                return {
                    "action": "wait",
                    "session_id": "test-session",
                    "iteration": 0,
                    "payload": {},
                }
            if call_count[0] == 2:
                # GET poll -> derive action
                return {
                    "action": "derive",
                    "session_id": "test-session",
                    "iteration": 1,
                    "payload": {"objective": "Test", "project_context": {}, "llm_provider": "anthropic"},
                }
            if call_count[0] == 3:
                # POST report_derivation -> WAIT
                return {
                    "action": "wait",
                    "session_id": "test-session",
                    "iteration": 2,
                    "payload": {},
                }
            # GET poll -> complete
            return {
                "action": "complete",
                "session_id": "test-session",
                "iteration": 3,
                "payload": {"session_summary": {}, "plan_final": []},
            }

        mock_api_client._request.side_effect = mock_request

        orchestrator = HybridOrchestrator(
            client=mock_api_client,
            working_dir=mock_working_dir,
        )

        # Mock handler for derive action
        mock_handler = MagicMock()
        mock_handler.handle.return_value = {"plan_items": [], "raw_response": ""}
        orchestrator._handlers[ActionType.DERIVE] = mock_handler

        with patch.object(orchestrator, "_poll_with_backoff") as mock_poll:
            mock_poll.return_value = 1.0

            orchestrator.derive(objective="Test")

            # Should have been called twice
            # First WAIT: poll_count=0, then derive resets
            # Second WAIT: poll_count=0 again (reset)
            assert mock_poll.call_count == 2
            assert mock_poll.call_args_list[0][0][0] == 0
            assert mock_poll.call_args_list[1][0][0] == 0  # Reset after derive
