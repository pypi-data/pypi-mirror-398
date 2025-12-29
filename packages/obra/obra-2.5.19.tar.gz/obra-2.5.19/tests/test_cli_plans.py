"""Tests for Obra CLI plan management commands.

Tests cover:
- upload-plan command: file validation, upload flow, error handling
- plans list command: plan listing, empty state
- plans delete command: deletion flow, confirmation
- run command: --plan-id and --plan-file flags

Uses typer.testing.CliRunner for isolated CLI testing.

Resource Limits (per docs/quality/testing/test-guidelines.md):
- Max sleep: 0.5s per test
- Max threads: 5 per test
- Max memory: 20KB per test
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from obra.cli import app

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

    with patch("obra.auth.get_current_auth", return_value=mock_auth_result), \
         patch("obra.auth.ensure_valid_token"):
        yield mock_auth_result


@pytest.fixture
def mock_api_client():
    """Mock APIClient for plan operations."""
    with patch("obra.api.APIClient") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.from_config.return_value = mock_instance

        # Configure upload_plan response
        mock_instance.upload_plan.return_value = {
            "plan_id": "test-plan-123",
            "name": "TEST-PLAN-001",
            "story_count": 3,
            "created_at": "2025-12-16T10:00:00Z",
        }

        # Configure list_plans response
        mock_instance.list_plans.return_value = [
            {
                "plan_id": "plan-001",
                "name": "FEAT-AUTH-001",
                "story_count": 5,
                "created_at": "2025-12-16T10:00:00Z",
            },
            {
                "plan_id": "plan-002",
                "name": "FEAT-API-001",
                "story_count": 3,
                "created_at": "2025-12-15T09:00:00Z",
            },
        ]

        # Configure get_plan response
        mock_instance.get_plan.return_value = {
            "plan_id": "test-plan-123",
            "name": "TEST-PLAN-001",
            "story_count": 3,
            "created_at": "2025-12-16T10:00:00Z",
        }

        # Configure delete_plan response
        mock_instance.delete_plan.return_value = {
            "success": True,
            "plan_id": "test-plan-123",
        }

        yield mock_instance


@pytest.fixture
def sample_plan_file(tmp_path: Path) -> Path:
    """Create a valid sample plan file for testing."""
    plan_content = {
        "work_id": "TEST-PLAN-001",
        "stories": [
            {
                "id": "S1",
                "title": "Story 1",
                "status": "pending",
                "tasks": [
                    {"id": "S1.T1", "desc": "Task 1", "status": "pending"}
                ],
            },
            {
                "id": "S2",
                "title": "Story 2",
                "status": "completed",
                "tasks": [
                    {"id": "S2.T1", "desc": "Task 1", "status": "completed"}
                ],
            },
        ],
    }

    plan_file = tmp_path / "test_plan.yaml"
    with open(plan_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(plan_content, f)

    return plan_file


@pytest.fixture
def invalid_plan_file(tmp_path: Path) -> Path:
    """Create an invalid plan file for testing validation."""
    plan_content = {
        "stories": [  # Missing work_id
            {
                "id": "S1",
                "title": "Story 1",
                # Missing status
            }
        ]
    }

    plan_file = tmp_path / "invalid_plan.yaml"
    with open(plan_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(plan_content, f)

    return plan_file


# =============================================================================
# Upload Plan Command Tests
# =============================================================================


class TestUploadPlanCommand:
    """Tests for the upload-plan command."""

    def test_upload_plan_shows_help(self, cli_runner: CliRunner) -> None:
        """Test that upload-plan --help shows usage information."""
        result = cli_runner.invoke(app, ["plans", "upload", "--help"])

        assert result.exit_code == 0
        assert "Upload a MACHINE_PLAN.yaml file" in result.stdout
        assert "--validate-only" in result.stdout

    def test_upload_plan_requires_file_path(self, cli_runner: CliRunner) -> None:
        """Test that upload-plan requires a file path argument."""
        result = cli_runner.invoke(app, ["plans", "upload"])

        assert result.exit_code != 0
        output = result.output or result.stdout
        assert "Missing argument" in output or "FILE_PATH" in output

    def test_upload_plan_validates_file(
        self,
        cli_runner: CliRunner,
        sample_plan_file: Path,
    ) -> None:
        """Test that upload-plan parses and uploads a valid plan file."""
        with patch("obra.cli_commands.upload_plan.get_current_auth") as mock_auth, \
             patch("obra.cli_commands.upload_plan.ensure_valid_token"), \
             patch("obra.cli_commands.upload_plan.APIClient.from_config") as mock_api:
            mock_auth.return_value = MagicMock(email="test@example.com")
            mock_client = MagicMock()
            mock_client.upload_plan.return_value = {"plan_id": "test-plan-123"}
            mock_api.return_value = mock_client
            result = cli_runner.invoke(app, ["plans", "upload", str(sample_plan_file)])

        assert result.exit_code == 0
        mock_client.upload_plan.assert_called_once()

    def test_upload_plan_fails_on_invalid_file(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test that upload-plan fails with invalid YAML."""
        invalid_yaml = tmp_path / "invalid.yaml"
        invalid_yaml.write_text("work_id: TEST\n  invalid indentation\nstories: [", encoding="utf-8")
        result = cli_runner.invoke(app, ["plans", "upload", str(invalid_yaml)])

        assert result.exit_code == 1
        assert "Failed to parse YAML" in result.stdout

    def test_upload_plan_validate_only_mode(
        self,
        cli_runner: CliRunner,
        sample_plan_file: Path,
    ) -> None:
        """Test upload-plan --validate-only skips upload."""
        with patch("obra.api.APIClient.from_config") as mock_api:
            result = cli_runner.invoke(
                app, ["plans", "upload", "--validate-only", str(sample_plan_file)]
            )

        assert result.exit_code == 0
        assert "YAML syntax is valid" in result.stdout
        assert "Full schema validation happens on server" in result.stdout
        mock_api.assert_not_called()


# =============================================================================
# Plans List Command Tests
# =============================================================================


class TestPlansListCommand:
    """Tests for the plans list command."""

    def test_plans_list_shows_help(self, cli_runner: CliRunner) -> None:
        """Test that plans list --help shows usage information."""
        result = cli_runner.invoke(app, ["plans", "list", "--help"])

        assert result.exit_code == 0
        assert "List uploaded plan files" in result.stdout
        assert "--limit" in result.stdout

    def test_plans_list_requires_auth(self, cli_runner: CliRunner) -> None:
        """Test that plans list requires authentication."""
        with patch("obra.auth.get_current_auth", return_value=None):
            result = cli_runner.invoke(app, ["plans", "list"])

            assert result.exit_code == 1
            assert "Not logged in" in result.stdout

    def test_plans_list_displays_plans(
        self, cli_runner: CliRunner, mock_auth, mock_api_client
    ) -> None:
        """Test that plans list displays uploaded plans."""
        result = cli_runner.invoke(app, ["plans", "list"])

        assert result.exit_code == 0
        assert "FEAT-AUTH-001" in result.stdout
        assert "FEAT-API-001" in result.stdout

    def test_plans_list_empty_state(
        self, cli_runner: CliRunner, mock_auth, mock_api_client
    ) -> None:
        """Test plans list with no uploaded plans."""
        mock_api_client.list_plans.return_value = []

        result = cli_runner.invoke(app, ["plans", "list"])

        assert result.exit_code == 0
        assert "No plans uploaded" in result.stdout


# =============================================================================
# Plans Delete Command Tests
# =============================================================================


class TestPlansDeleteCommand:
    """Tests for the plans delete command."""

    def test_plans_delete_shows_help(self, cli_runner: CliRunner) -> None:
        """Test that plans delete --help shows usage information."""
        result = cli_runner.invoke(app, ["plans", "delete", "--help"])

        assert result.exit_code == 0
        assert "Delete an uploaded plan" in result.stdout
        assert "--force" in result.stdout

    def test_plans_delete_requires_plan_id(self, cli_runner: CliRunner) -> None:
        """Test that plans delete requires a plan_id argument."""
        result = cli_runner.invoke(app, ["plans", "delete"])

        assert result.exit_code != 0
        output = result.output or result.stdout
        assert "Missing argument" in output or "PLAN_ID" in output

    def test_plans_delete_requires_auth(self, cli_runner: CliRunner) -> None:
        """Test that plans delete requires authentication."""
        with patch("obra.auth.get_current_auth", return_value=None):
            result = cli_runner.invoke(app, ["plans", "delete", "test-plan-123"])

            assert result.exit_code == 1
            assert "Not logged in" in result.stdout

    def test_plans_delete_with_force_flag(
        self, cli_runner: CliRunner, mock_auth, mock_api_client
    ) -> None:
        """Test plans delete with --force skips confirmation."""
        result = cli_runner.invoke(
            app, ["plans", "delete", "test-plan-123", "--force"]
        )

        assert result.exit_code == 0
        assert "Plan deleted" in result.stdout
        mock_api_client.delete_plan.assert_called_once_with("test-plan-123")


# =============================================================================
# Run Command with Plan Flags Tests
# =============================================================================


class TestRunCommandWithPlans:
    """Tests for run command with plan-related flags."""

    def test_run_with_plan_id_flag(self, cli_runner: CliRunner) -> None:
        """Test that run accepts --plan-id flag."""
        result = cli_runner.invoke(
            app, ["run", "--help"]
        )

        assert result.exit_code == 0
        assert "--plan-id" in result.stdout

    def test_run_with_plan_file_flag(self, cli_runner: CliRunner) -> None:
        """Test that run accepts --plan-file flag."""
        result = cli_runner.invoke(
            app, ["run", "--help"]
        )

        assert result.exit_code == 0
        assert "--plan-file" in result.stdout

    def test_run_rejects_both_plan_flags(self, cli_runner: CliRunner) -> None:
        """Test that run rejects both --plan-id and --plan-file."""
        with tempfile.NamedTemporaryFile(suffix=".yaml") as tmp:
            result = cli_runner.invoke(
                app,
                [
                    "run",
                    "--plan-id", "test-plan",
                    "--plan-file", tmp.name,
                    "Test objective"
                ]
            )

            assert result.exit_code == 2  # Config error
            assert "Cannot specify both" in result.stdout


# =============================================================================
# C15: Plan File Validation Tests
# =============================================================================


class TestPlanFileValidationC15:
    """Tests for comprehensive plan file validation (C15).

    Validates the C15 enhancements:
    - File existence checks
    - File readability checks
    - YAML parsing with clear error messages
    - Type validation (dict vs list vs None)
    - Empty file handling
    """

    def test_plan_file_not_found(
        self, cli_runner: CliRunner, mock_auth, mock_api_client, tmp_path: Path
    ) -> None:
        """Test that run fails gracefully when plan file doesn't exist."""
        nonexistent_file = tmp_path / "nonexistent.yaml"

        result = cli_runner.invoke(
            app,
            ["run", "--plan-file", str(nonexistent_file), "Test objective"]
        )

        assert result.exit_code == 1
        assert "Plan file not found" in result.stdout

    def test_plan_file_invalid_yaml_syntax(
        self, cli_runner: CliRunner, mock_auth, mock_api_client, tmp_path: Path
    ) -> None:
        """Test that run fails with clear error on invalid YAML syntax."""
        invalid_yaml = tmp_path / "invalid.yaml"
        with open(invalid_yaml, "w", encoding="utf-8") as f:
            f.write("work_id: TEST\n  invalid indentation\nstories: [")

        result = cli_runner.invoke(
            app,
            ["run", "--plan-file", str(invalid_yaml), "Test objective"]
        )

        assert result.exit_code == 1
        assert "Invalid YAML syntax" in result.stdout

    def test_plan_file_empty(
        self, cli_runner: CliRunner, mock_auth, mock_api_client, tmp_path: Path
    ) -> None:
        """Test that run fails gracefully with empty plan file."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("", encoding="utf-8")

        result = cli_runner.invoke(
            app,
            ["run", "--plan-file", str(empty_file), "Test objective"]
        )

        assert result.exit_code == 1
        assert "Plan file is empty" in result.stdout

    def test_plan_file_wrong_type_list(
        self, cli_runner: CliRunner, mock_auth, mock_api_client, tmp_path: Path
    ) -> None:
        """Test that run fails when plan file contains list instead of dict."""
        list_file = tmp_path / "list.yaml"
        with open(list_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(["item1", "item2"], f)

        result = cli_runner.invoke(
            app,
            ["run", "--plan-file", str(list_file), "Test objective"]
        )

        assert result.exit_code == 1
        assert "must contain a YAML dictionary" in result.stdout
        assert "got list" in result.stdout

    def test_plan_file_wrong_type_string(
        self, cli_runner: CliRunner, mock_auth, mock_api_client, tmp_path: Path
    ) -> None:
        """Test that run fails when plan file contains plain string."""
        string_file = tmp_path / "string.yaml"
        string_file.write_text("just a plain string", encoding="utf-8")

        result = cli_runner.invoke(
            app,
            ["run", "--plan-file", str(string_file), "Test objective"]
        )

        assert result.exit_code == 1
        assert "must contain a YAML dictionary" in result.stdout
        assert "got str" in result.stdout

    def test_plan_file_encoding_error(
        self, cli_runner: CliRunner, mock_auth, mock_api_client, tmp_path: Path
    ) -> None:
        """Test that run fails gracefully with non-UTF-8 encoding."""
        binary_file = tmp_path / "binary.yaml"
        # Write invalid UTF-8 bytes
        with open(binary_file, "wb") as f:
            f.write(b"\xff\xfe\x00\x00Invalid UTF-8")

        result = cli_runner.invoke(
            app,
            ["run", "--plan-file", str(binary_file), "Test objective"]
        )

        assert result.exit_code == 1
        assert "encoding error" in result.stdout.lower()

    def test_plan_file_valid_passes_validation(
        self, cli_runner: CliRunner, mock_auth, sample_plan_file: Path
    ) -> None:
        """Test that valid plan file passes all C15 validations."""
        with patch("obra.api.APIClient.from_config") as mock_api:
            mock_client = MagicMock()
            mock_api.return_value = mock_client
            mock_client.upload_plan.return_value = {"plan_id": "test-plan-123"}

            with patch("obra.config.validate_provider_ready"):
                result = cli_runner.invoke(
                    app,
                    ["run", "--plan-file", str(sample_plan_file), "Test objective"]
                )

                # Should pass C15 validation checks
                # (will fail later during session execution, but that's ok)
                assert "Plan file not found" not in result.stdout
                assert "Invalid YAML" not in result.stdout
                assert "Plan file is empty" not in result.stdout
                assert "must contain a YAML dictionary" not in result.stdout

                # Verify upload was attempted (proves validation passed)
                mock_client.upload_plan.assert_called_once()
