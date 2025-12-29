"""Integration tests for CLI isolation flags.

Tests verify that --isolated, --no-isolated flags, OBRA_ISOLATED env var,
CI environment detection, and config file settings are correctly handled
with proper precedence.

Related:
    - EPIC-ISOLATION-001: Session Isolation
    - obra/cli.py:326-378 (_should_isolate function)
    - obra/config/__init__.py (get_isolated_mode, set_isolated_mode)
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from obra.cli import _should_isolate
from obra.config import get_isolated_mode, set_isolated_mode


class TestShouldIsolateFunction:
    """Test suite for _should_isolate() function precedence logic."""

    @pytest.fixture(autouse=True)
    def clean_env(self):
        """Clean up environment variables before/after each test."""
        # Store original values
        orig_obra_isolated = os.environ.pop("OBRA_ISOLATED", None)
        orig_ci = os.environ.pop("CI", None)

        yield

        # Restore original values
        if orig_obra_isolated is not None:
            os.environ["OBRA_ISOLATED"] = orig_obra_isolated
        else:
            os.environ.pop("OBRA_ISOLATED", None)

        if orig_ci is not None:
            os.environ["CI"] = orig_ci
        else:
            os.environ.pop("CI", None)

    @pytest.fixture
    def mock_config_isolated_none(self):
        """Mock config to return None for isolated_mode."""
        with patch("obra.config.get_isolated_mode", return_value=None):
            yield

    @pytest.fixture
    def mock_config_isolated_true(self):
        """Mock config to return True for isolated_mode."""
        with patch("obra.config.get_isolated_mode", return_value=True):
            yield

    @pytest.fixture
    def mock_config_isolated_false(self):
        """Mock config to return False for isolated_mode."""
        with patch("obra.config.get_isolated_mode", return_value=False):
            yield

    # =========================================================================
    # Priority 1: CLI Flags Tests
    # =========================================================================

    def test_cli_isolated_flag_returns_true(self, mock_config_isolated_none):
        """--isolated flag should return True regardless of other settings."""
        assert _should_isolate(isolated=True) is True
        assert _should_isolate(isolated=True, no_isolated=None) is True

    def test_cli_no_isolated_flag_returns_false(self, mock_config_isolated_none):
        """--no-isolated flag should return False regardless of other settings."""
        assert _should_isolate(no_isolated=True) is False
        assert _should_isolate(isolated=None, no_isolated=True) is False

    def test_cli_isolated_overrides_env_and_config(self, mock_config_isolated_false):
        """--isolated should override env var and config settings."""
        os.environ["OBRA_ISOLATED"] = "false"
        assert _should_isolate(isolated=True) is True

    def test_cli_no_isolated_overrides_env_and_config(self, mock_config_isolated_true):
        """--no-isolated should override env var and config settings."""
        os.environ["OBRA_ISOLATED"] = "true"
        os.environ["CI"] = "true"
        assert _should_isolate(no_isolated=True) is False

    # =========================================================================
    # Priority 2: Environment Variable OBRA_ISOLATED Tests
    # =========================================================================

    def test_env_obra_isolated_true_values(self, mock_config_isolated_none):
        """OBRA_ISOLATED=true/1/yes should enable isolation."""
        for value in ("true", "True", "TRUE", "1", "yes", "YES"):
            os.environ["OBRA_ISOLATED"] = value
            assert _should_isolate() is True, f"Failed for OBRA_ISOLATED={value}"

    def test_env_obra_isolated_false_values(self, mock_config_isolated_none):
        """OBRA_ISOLATED=false/0/no should disable isolation."""
        for value in ("false", "False", "FALSE", "0", "no", "NO"):
            os.environ["OBRA_ISOLATED"] = value
            assert _should_isolate() is False, f"Failed for OBRA_ISOLATED={value}"

    def test_env_obra_isolated_overrides_ci(self, mock_config_isolated_none):
        """OBRA_ISOLATED should override CI environment detection."""
        os.environ["CI"] = "true"
        os.environ["OBRA_ISOLATED"] = "false"
        assert _should_isolate() is False

    # =========================================================================
    # Priority 3: CI Environment Detection Tests
    # =========================================================================

    def test_ci_true_enables_isolation(self, mock_config_isolated_none):
        """CI=true should enable isolation by default."""
        os.environ["CI"] = "true"
        assert _should_isolate() is True

    def test_ci_true_values(self, mock_config_isolated_none):
        """Various CI=true value formats should enable isolation."""
        for value in ("true", "True", "TRUE", "1", "yes"):
            os.environ["CI"] = value
            assert _should_isolate() is True, f"Failed for CI={value}"

    def test_ci_false_falls_through_to_default(self, mock_config_isolated_none):
        """CI=false should fall through to default (which is now True)."""
        os.environ["CI"] = "false"
        assert _should_isolate() is True  # Default is now True

    def test_no_isolated_overrides_ci(self, mock_config_isolated_none):
        """--no-isolated should override CI=true environment."""
        os.environ["CI"] = "true"
        assert _should_isolate(no_isolated=True) is False

    # =========================================================================
    # Priority 4: Config File Tests
    # =========================================================================

    def test_config_isolated_true(self, mock_config_isolated_true):
        """Config agent.isolated_mode=true should enable isolation."""
        assert _should_isolate() is True

    def test_config_isolated_false(self, mock_config_isolated_false):
        """Config agent.isolated_mode=false should disable isolation."""
        assert _should_isolate() is False

    def test_config_overridden_by_env(self, mock_config_isolated_true):
        """Config should be overridden by OBRA_ISOLATED env var."""
        os.environ["OBRA_ISOLATED"] = "false"
        assert _should_isolate() is False

    # =========================================================================
    # Priority 5: Default Behavior Tests
    # =========================================================================

    def test_default_isolation_enabled(self, mock_config_isolated_none):
        """Default (no flags, no env, no config) should return True for reproducibility."""
        assert _should_isolate() is True

    def test_default_with_empty_args(self, mock_config_isolated_none):
        """Default with explicit None args should return True for reproducibility."""
        assert _should_isolate(isolated=None, no_isolated=None) is True


class TestConfigFunctions:
    """Test suite for config get/set functions."""

    @pytest.fixture
    def mock_config_file(self, tmp_path):
        """Use a temporary config file for testing."""
        config_path = tmp_path / ".obra" / "client-config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with patch("obra.config.CONFIG_PATH", config_path):
            yield config_path

    def test_get_isolated_mode_none_when_not_set(self, mock_config_file):
        """get_isolated_mode returns None when not configured."""
        assert get_isolated_mode() is None

    def test_set_and_get_isolated_mode_true(self, mock_config_file):
        """set_isolated_mode(True) should be retrievable."""
        set_isolated_mode(True)
        assert get_isolated_mode() is True

    def test_set_and_get_isolated_mode_false(self, mock_config_file):
        """set_isolated_mode(False) should be retrievable."""
        set_isolated_mode(False)
        assert get_isolated_mode() is False

    def test_set_isolated_mode_none_clears(self, mock_config_file):
        """set_isolated_mode(None) should clear the setting."""
        set_isolated_mode(True)
        assert get_isolated_mode() is True
        set_isolated_mode(None)
        assert get_isolated_mode() is None
