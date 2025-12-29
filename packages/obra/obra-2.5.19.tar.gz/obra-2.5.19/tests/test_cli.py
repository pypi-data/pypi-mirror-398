"""Tests for Obra CLI commands.

Tests cover:
- run command: argument parsing, help text, option handling
- status command: session status display
- resume command: session resumption
- version command: version display and server check
- config command: configuration management

Uses typer.testing.CliRunner for isolated CLI testing.

Resource Limits (per docs/quality/testing/test-guidelines.md):
- Max sleep: 0.5s per test
- Max threads: 5 per test
- Max memory: 20KB per test
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from obra.api.protocol import CompletionNotice
from obra.cli import app, config as config_command

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CliRunner for testing commands."""
    return CliRunner()


@pytest.fixture
def mock_auth():
    """Mock authentication to bypass login checks."""
    mock_auth_result = MagicMock()
    mock_auth_result.email = "test@example.com"
    mock_auth_result.display_name = "Test User"
    mock_auth_result.firebase_uid = "test-uid-12345678"
    mock_auth_result.auth_provider = "google"

    # Patch at the source modules
    with patch("obra.auth.get_current_auth", return_value=mock_auth_result), \
         patch("obra.auth.ensure_valid_token"):
        yield mock_auth_result


@pytest.fixture
def mock_orchestrator():
    """Mock HybridOrchestrator for run/resume tests."""
    with patch("obra.hybrid.HybridOrchestrator") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.from_config.return_value = mock_instance

        # Configure derive to return a complete result
        mock_result = MagicMock()
        mock_result.action = "complete"
        mock_result.session_summary = {
            "items_completed": 3,
            "total_iterations": 5,
            "quality_score": 0.92,
        }
        mock_instance.derive.return_value = mock_result
        mock_instance.resume.return_value = mock_result

        yield mock_instance


# =============================================================================
# Run Command Tests
# =============================================================================


class TestRunCommand:
    """Tests for the run command."""

    def test_run_shows_help(self, cli_runner: CliRunner) -> None:
        """Test that run --help shows usage information."""
        result = cli_runner.invoke(app, ["run", "--help"])

        assert result.exit_code == 0
        assert "Run AI-orchestrated workflow for an objective" in result.stdout
        assert "--dir" in result.stdout or "-d" in result.stdout
        assert "--model" in result.stdout or "-m" in result.stdout
        assert "--thinking-level" in result.stdout or "-t" in result.stdout
        assert "--verbose" in result.stdout or "-v" in result.stdout

    def test_run_requires_objective(self, cli_runner: CliRunner) -> None:
        """Test that run requires an objective argument."""
        result = cli_runner.invoke(app, ["run"])

        assert result.exit_code != 0
        # Typer shows missing argument error (may be in output which combines stdout/stderr)
        output = result.output or result.stdout
        assert "Missing argument" in output or "OBJECTIVE" in output

    def test_run_invalid_thinking_level(self, cli_runner: CliRunner) -> None:
        """Test that run rejects invalid thinking levels."""
        result = cli_runner.invoke(app, [
            "run",
            "Test objective",
            "--thinking-level", "super_maximum",
        ])

        assert result.exit_code == 2  # Config error exit code
        assert "Invalid thinking level" in result.stdout

    def test_run_valid_thinking_levels(self, cli_runner: CliRunner, mock_auth, mock_orchestrator, tmp_path: Path) -> None:
        """Test that run accepts all valid thinking levels."""
        valid_levels = ["off", "low", "medium", "high", "maximum"]

        with (
            patch("obra.config.validate_provider_ready"),
            patch("obra.cli._resolve_repo_root", return_value=None),
        ):
            for level in valid_levels:
                result = cli_runner.invoke(app, [
                    "run",
                    "Test objective",
                    "--thinking-level", level,
                    "--dir", str(tmp_path),
                ])

                # Should not fail on invalid thinking level
                assert "Invalid thinking level" not in result.stdout

    def test_run_working_dir_not_exists(self, cli_runner: CliRunner, mock_auth) -> None:
        """Test that run fails if working directory doesn't exist."""
        with patch("obra.config.validate_provider_ready"):
            result = cli_runner.invoke(app, [
                "run",
                "Test objective",
                "--dir", "/nonexistent/path/that/does/not/exist",
            ])

        assert result.exit_code == 1
        assert "does not exist" in result.stdout

    def test_run_success(
        self,
        cli_runner: CliRunner,
        mock_auth,
        mock_orchestrator,
        tmp_path: Path,
    ) -> None:
        """Test successful run execution."""
        with (
            patch("obra.config.validate_provider_ready"),
            patch("obra.cli._resolve_repo_root", return_value=None),
        ):
            result = cli_runner.invoke(app, [
                "run",
                "Add user authentication",
                "--dir", str(tmp_path),
            ])

        assert result.exit_code == 0
        assert "completed successfully" in result.stdout
        mock_orchestrator.derive.assert_called_once_with(
            "Add user authentication",
            plan_id=None,
            plan_only=False,
            project_id=None,
            repo_root=None,
        )

    def test_run_handles_completion_notice(
        self,
        cli_runner: CliRunner,
        mock_auth,
        tmp_path: Path,
    ) -> None:
        """Test run handles CompletionNotice without crashing."""
        completion = CompletionNotice(
            items_completed=1,
            total_iterations=2,
            quality_score=0.5,
        )

        with (
            patch("obra.hybrid.HybridOrchestrator") as mock_cls,
            patch("obra.config.validate_provider_ready"),
            patch("obra.cli._resolve_repo_root", return_value=None),
        ):
            mock_instance = MagicMock()
            mock_instance.derive.return_value = completion
            mock_cls.from_config.return_value = mock_instance

            result = cli_runner.invoke(app, [
                "run",
                "Test objective",
                "--dir", str(tmp_path),
            ])

        assert result.exit_code == 0
        assert "completed successfully" in result.stdout

    def test_run_passes_model_to_orchestrator(
        self,
        cli_runner: CliRunner,
        mock_auth,
        tmp_path: Path,
    ) -> None:
        """Test that --model option is passed to orchestrator."""
        with (
            patch("obra.hybrid.HybridOrchestrator") as mock_cls,
            patch("obra.config.validate_provider_ready"),
            patch("obra.cli._resolve_repo_root", return_value=None),
        ):
            mock_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.action = "complete"
            mock_instance.derive.return_value = mock_result
            mock_cls.from_config.return_value = mock_instance

            cli_runner.invoke(app, [
                "run",
                "Test objective",
                "--dir", str(tmp_path),
                "--model", "opus",
            ])

            # Check that from_config was called with impl_model="opus"
            call_kwargs = mock_cls.from_config.call_args.kwargs
            assert call_kwargs.get("impl_model") == "opus"

    def test_run_passes_project_id_to_orchestrator(
        self,
        cli_runner: CliRunner,
        mock_auth,
        mock_orchestrator,
        tmp_path: Path,
    ) -> None:
        """Test that --project option is passed to orchestrator."""
        with (
            patch("obra.config.validate_provider_ready"),
            patch("obra.cli._resolve_repo_root", return_value=None),
        ):
            result = cli_runner.invoke(app, [
                "run",
                "Test objective",
                "--dir", str(tmp_path),
                "--project", "project-123",
            ])

        assert result.exit_code == 0
        mock_orchestrator.derive.assert_called_once_with(
            "Test objective",
            plan_id=None,
            plan_only=False,
            project_id="project-123",
            repo_root=None,
        )


# =============================================================================
# Status Command Tests
# =============================================================================


class TestStatusCommand:
    """Tests for the status command."""

    def test_status_shows_help(self, cli_runner: CliRunner) -> None:
        """Test that status --help shows usage information."""
        result = cli_runner.invoke(app, ["status", "--help"])

        assert result.exit_code == 0
        assert "Check the status of a derivation session" in result.stdout
        assert "SESSION_ID" in result.stdout

    def test_status_requires_auth(self, cli_runner: CliRunner) -> None:
        """Test that status requires authentication."""
        with patch("obra.auth.get_current_auth", return_value=None):
            result = cli_runner.invoke(app, ["status"])

        assert result.exit_code == 1
        assert "Not logged in" in result.stdout

    def test_status_no_sessions(self, cli_runner: CliRunner, mock_auth) -> None:
        """Test status when no sessions exist."""
        with patch("obra.api.APIClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.list_sessions.return_value = []
            mock_client_cls.from_config.return_value = mock_client

            result = cli_runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "No active sessions" in result.stdout

    def test_status_displays_session(self, cli_runner: CliRunner, mock_auth) -> None:
        """Test that status displays session information."""
        with patch("obra.api.APIClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.list_sessions.return_value = [{
                "session_id": "session-123",
                "objective": "Test objective",
                "state": "running",
                "current_phase": "execute",
                "iteration": 3,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T01:00:00Z",
            }]
            mock_client_cls.from_config.return_value = mock_client

            result = cli_runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "Session Status" in result.stdout
        assert "session-123" in result.stdout
        assert "Test objective" in result.stdout
        assert "execute" in result.stdout

    def test_status_by_session_id(self, cli_runner: CliRunner, mock_auth) -> None:
        """Test status retrieval by specific session ID."""
        with patch("obra.api.APIClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_session.return_value = {
                "session_id": "specific-session",
                "objective": "Specific task",
                "state": "completed",
                "current_phase": "done",
                "iteration": 5,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T02:00:00Z",
            }
            mock_client_cls.from_config.return_value = mock_client

            result = cli_runner.invoke(app, [
                "status",
                "specific-session",
            ])

        assert result.exit_code == 0
        mock_client.get_session.assert_called_once_with("specific-session")
        assert "specific-session" in result.stdout


# =============================================================================
# Resume Command Tests
# =============================================================================


class TestResumeCommand:
    """Tests for the resume command."""

    def test_resume_shows_help(self, cli_runner: CliRunner) -> None:
        """Test that resume --help shows usage information."""
        result = cli_runner.invoke(app, ["resume", "--help"])

        assert result.exit_code == 0
        assert "Resume an interrupted session" in result.stdout
        assert "SESSION_ID" in result.stdout

    def test_resume_requires_session_id(self, cli_runner: CliRunner) -> None:
        """Test that resume requires a session ID argument."""
        result = cli_runner.invoke(app, ["resume"])

        assert result.exit_code != 0
        # Typer shows missing argument error (may be in output which combines stdout/stderr)
        output = result.output or result.stdout
        assert "Missing argument" in output or "SESSION_ID" in output

    def test_resume_requires_auth(self, cli_runner: CliRunner) -> None:
        """Test that resume requires authentication."""
        with patch("obra.auth.get_current_auth", return_value=None):
            result = cli_runner.invoke(app, ["resume", "session-123"])

        assert result.exit_code == 1
        assert "Not logged in" in result.stdout

    def test_resume_success(
        self,
        cli_runner: CliRunner,
        mock_auth,
        mock_orchestrator,
    ) -> None:
        """Test successful resume execution."""
        result = cli_runner.invoke(app, ["resume", "session-123"])

        assert result.exit_code == 0
        assert "completed successfully" in result.stdout
        mock_orchestrator.resume.assert_called_once_with("session-123")

    def test_resume_handles_completion_notice(
        self,
        cli_runner: CliRunner,
        mock_auth,
    ) -> None:
        """Test resume handles CompletionNotice without crashing."""
        completion = CompletionNotice(
            items_completed=2,
            total_iterations=3,
            quality_score=0.7,
        )

        with patch("obra.hybrid.HybridOrchestrator") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.resume.return_value = completion
            mock_cls.from_config.return_value = mock_instance

            result = cli_runner.invoke(app, ["resume", "session-456"])

        assert result.exit_code == 0
        assert "completed successfully" in result.stdout

    def test_resume_with_stream(
        self,
        cli_runner: CliRunner,
        mock_auth,
        mock_orchestrator,
    ) -> None:
        """Test resume with streaming enabled."""
        result = cli_runner.invoke(app, [
            "resume",
            "session-123",
            "--stream",
        ])

        assert result.exit_code == 0


# =============================================================================
# Version Command Tests
# =============================================================================


class TestVersionCommand:
    """Tests for the version command."""

    def test_version_displays_info(self, cli_runner: CliRunner) -> None:
        """Test that version shows version information."""
        result = cli_runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "Obra" in result.stdout
        assert "Python:" in result.stdout
        assert "Platform:" in result.stdout

    def test_version_check_server(self, cli_runner: CliRunner) -> None:
        """Test version --check attempts server connection."""
        with patch("obra.api.APIClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get_version.return_value = {
                "version": "1.0.0",
                "api_version": "v1",
                "status": "healthy",
                "compatible": True,
            }
            mock_client_cls.return_value = mock_client

            result = cli_runner.invoke(app, ["version", "--check"])

        assert result.exit_code == 0
        assert "Server Information" in result.stdout or "compatible" in result.stdout.lower()


# =============================================================================
# Config Command Tests
# =============================================================================


class TestConfigCommand:
    """Tests for the config command."""

    def test_config_shows_help(self, cli_runner: CliRunner) -> None:
        """Test that config --help shows usage information."""
        result = cli_runner.invoke(app, ["config", "--help"])

        assert result.exit_code == 0
        assert "Manage Obra configuration" in result.stdout
        assert "--show" in result.stdout
        assert "--get" in result.stdout
        assert "--set" in result.stdout
        assert "--reset" in result.stdout
        assert "--validate" in result.stdout

    def test_config_show(self, cli_runner: CliRunner) -> None:
        """Test config --show displays current configuration."""
        with patch("obra.config.load_config") as mock_load:
            mock_load.return_value = {
                "api_base_url": "https://api.obra.dev",
                "default_provider": "anthropic",
            }

            result = cli_runner.invoke(app, ["config", "--show"])

        assert result.exit_code == 0
        assert "api_base_url: https://api.obra.dev" in result.stdout

    def test_config_show_empty(self, cli_runner: CliRunner) -> None:
        """Test config --show with no configuration set."""
        with patch("obra.config.load_config") as mock_load, \
             patch("obra.config.CONFIG_PATH") as mock_path:
            mock_load.return_value = {}
            mock_path.exists.return_value = False

            result = cli_runner.invoke(app, ["config", "--show"])

        assert result.exit_code == 0
        assert "llm.orchestrator.provider: anthropic" in result.stdout

    def test_config_validate(self, cli_runner: CliRunner) -> None:
        """Test config --validate checks provider CLIs."""
        with patch("obra.config.check_provider_status") as mock_check, \
             patch("obra.config.load_config") as mock_load:
            mock_status = MagicMock()
            mock_status.installed = True
            mock_status.cli_command = "claude"
            mock_status.install_hint = ""
            mock_status.docs_url = ""
            mock_check.return_value = mock_status
            mock_load.return_value = {}

            result = cli_runner.invoke(app, ["config", "--validate"])

        assert result.exit_code == 0
        assert "Configuration Validation" in result.stdout or "Provider" in result.stdout

    def test_config_validate_json(self, cli_runner: CliRunner) -> None:
        """Test config --validate --json outputs JSON."""
        with patch("obra.config.check_provider_status") as mock_check, \
             patch("obra.config.load_config") as mock_load:
            mock_status = MagicMock()
            mock_status.installed = True
            mock_status.cli_command = "claude"
            mock_status.install_hint = ""
            mock_status.docs_url = ""
            mock_check.return_value = mock_status
            mock_load.return_value = {}

            result = cli_runner.invoke(app, ["config", "--validate", "--json"])

        assert result.exit_code == 0
        # Should be valid JSON
        import json
        output = json.loads(result.stdout)
        assert "status" in output
        assert "providers" in output

    def test_config_get_unknown_path(self, cli_runner: CliRunner) -> None:
        """Test config --get rejects unknown paths."""
        result = cli_runner.invoke(app, ["config", "--get", "invalid.path"])

        assert result.exit_code == 1
        output = result.output or result.stdout
        assert "Unknown config path" in output

    def test_config_set_missing_value(self, cli_runner: CliRunner) -> None:
        """Test config --set requires a value."""
        result = cli_runner.invoke(app, ["config", "--set", "llm.orchestrator.provider"])

        assert result.exit_code == 2
        output = result.output or result.stdout
        assert "Missing value" in output

    def test_config_show_json(self, cli_runner: CliRunner) -> None:
        """Test config --show --json outputs config payload."""
        with patch("obra.config.load_config") as mock_load, \
             patch("obra.config.CONFIG_PATH") as mock_path:
            mock_load.return_value = {}
            mock_path.exists.return_value = False

            result = cli_runner.invoke(app, ["config", "--show", "--json"])

        assert result.exit_code == 0
        import json
        output = json.loads(result.stdout)
        assert output["scope"] == "local"
        assert "data" in output

    def test_config_reset_cancelled(self, cli_runner: CliRunner) -> None:
        """Test config --reset can be cancelled."""
        result = cli_runner.invoke(app, ["config", "--reset"], input="n\n")

        assert result.exit_code == 0
        assert "Non-interactive mode" in result.stdout

    def test_config_reset_confirmed(self) -> None:
        """Test config --reset when confirmed."""
        with patch("obra.config.save_config") as mock_save, \
             patch("obra.cli.sys.stdin", new=MagicMock(isatty=lambda: True)), \
             patch("obra.cli.typer.confirm", return_value=True):
            config_command(
                show=False,
                get_path=None,
                set_path=None,
                set_value=None,
                reset=True,
                validate=False,
                json_output=False,
                confirm=False,
                scope="local",
                verbose=False,
            )

        mock_save.assert_called_once_with({})


# =============================================================================
# Authentication Command Tests
# =============================================================================


class TestAuthCommands:
    """Tests for authentication commands."""

    def test_whoami_not_logged_in(self, cli_runner: CliRunner) -> None:
        """Test whoami when not logged in."""
        with patch("obra.auth.get_current_auth", return_value=None):
            result = cli_runner.invoke(app, ["whoami"])

        assert result.exit_code == 0
        assert "Not logged in" in result.stdout

    def test_whoami_logged_in(self, cli_runner: CliRunner) -> None:
        """Test whoami when logged in."""
        mock_auth_result = MagicMock()
        mock_auth_result.email = "user@example.com"
        mock_auth_result.display_name = "Test User"
        mock_auth_result.firebase_uid = "uid-1234567890"
        mock_auth_result.auth_provider = "github"

        with patch("obra.auth.get_current_auth", return_value=mock_auth_result), \
             patch("obra.config.load_config", return_value={}):
            result = cli_runner.invoke(app, ["whoami"])

        assert result.exit_code == 0
        assert "Current User" in result.stdout
        assert "user@example.com" in result.stdout
        assert "Test User" in result.stdout
        assert "github" in result.stdout

    def test_logout_not_logged_in(self, cli_runner: CliRunner) -> None:
        """Test logout when not logged in."""
        with patch("obra.auth.get_current_auth", return_value=None):
            result = cli_runner.invoke(app, ["logout"])

        assert result.exit_code == 0
        assert "Not currently logged in" in result.stdout

    def test_logout_logged_in(self, cli_runner: CliRunner) -> None:
        """Test logout when logged in."""
        mock_auth_result = MagicMock()
        mock_auth_result.email = "user@example.com"

        with patch("obra.auth.get_current_auth", return_value=mock_auth_result), \
             patch("obra.auth.clear_auth") as mock_clear:
            result = cli_runner.invoke(app, ["logout"])

        assert result.exit_code == 0
        mock_clear.assert_called_once()
        assert "Logged out" in result.stdout


# =============================================================================
# App-Level Tests
# =============================================================================


class TestAppLevel:
    """Tests for app-level behavior."""

    def test_app_no_args_shows_help(self, cli_runner: CliRunner) -> None:
        """Test that running obra without arguments shows help."""
        result = cli_runner.invoke(app, [])

        # App is configured with no_args_is_help=True, which returns exit code 0 or 2
        # The important thing is it shows help content
        output = result.output or result.stdout
        # Should show available commands
        assert "run" in output
        assert "status" in output
        assert "login" in output

    def test_app_help(self, cli_runner: CliRunner) -> None:
        """Test that obra --help shows comprehensive help."""
        result = cli_runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Obra" in result.stdout
        assert "AI Orchestration" in result.stdout
