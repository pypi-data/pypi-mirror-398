"""Packaging smoke tests to verify wheel contents.

This module ensures that all critical modules are included in the
wheel distribution and importable after installation.

Regression tests:
    - ISSUE-SIM-20251216-002: Verify obra.security module is in wheel

Related:
    - docs/quality/investigations/ISSUE-SIM-20251216-002_RCA.md
    - obra/pyproject.toml (packages list)
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


def test_issue_sim_20251216_002_security_module_in_wheel():
    """Regression test: Verify obra.security is packaged in wheel.

    This test catches the root cause of ISSUE-SIM-20251216-002 where the
    obra.security module was missing from the PyPI distribution because
    it wasn't listed in pyproject.toml packages array.

    Expected Behavior:
        - BEFORE FIX: Wheel does not contain obra/security/ directory
        - AFTER FIX: Wheel contains obra/security/__init__.py and prompt_sanitizer.py

    Verification:
        1. Build a wheel from the current source
        2. Inspect wheel contents for obra/security/ files
        3. Verify both __init__.py and prompt_sanitizer.py are present
    """
    # Get the obra package directory (parent of tests/)
    obra_dir = Path(__file__).parent.parent
    assert (obra_dir / "pyproject.toml").exists(), "pyproject.toml not found"

    # Build a fresh wheel
    build_result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel"],
        check=False, cwd=obra_dir,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert build_result.returncode == 0, f"Wheel build failed: {build_result.stderr}"

    # Find the built wheel
    dist_dir = obra_dir / "dist"
    wheels = list(dist_dir.glob("obra-*.whl"))
    assert len(wheels) > 0, "No wheel file found in dist/"

    # Use the most recently created wheel
    wheel_path = max(wheels, key=lambda p: p.stat().st_mtime)

    # Inspect wheel contents for security module
    inspect_result = subprocess.run(
        [sys.executable, "-m", "zipfile", "-l", str(wheel_path)],
        check=False, capture_output=True,
        text=True,
        timeout=10,
    )

    assert inspect_result.returncode == 0, f"Wheel inspection failed: {inspect_result.stderr}"

    wheel_contents = inspect_result.stdout

    # Check for security module files
    # BEFORE FIX: These assertions will FAIL
    # AFTER FIX: These assertions will PASS
    assert "obra/security/__init__.py" in wheel_contents, (
        "obra/security/__init__.py not found in wheel - "
        "security module is missing from package distribution"
    )

    assert "obra/security/prompt_sanitizer.py" in wheel_contents, (
        "obra/security/prompt_sanitizer.py not found in wheel - "
        "security module is incomplete"
    )


def test_all_critical_modules_in_wheel():
    """Verify all critical obra subpackages are in the wheel.

    This is a comprehensive smoke test that checks for all essential modules
    to prevent future packaging issues like ISSUE-SIM-20251216-002.
    """
    # Get the obra package directory
    obra_dir = Path(__file__).parent.parent
    dist_dir = obra_dir / "dist"

    # Find the most recent wheel
    wheels = list(dist_dir.glob("obra-*.whl"))
    if not wheels:
        pytest.skip("No wheel found - run build first")

    wheel_path = max(wheels, key=lambda p: p.stat().st_mtime)

    # Inspect wheel contents
    inspect_result = subprocess.run(
        [sys.executable, "-m", "zipfile", "-l", str(wheel_path)],
        check=False, capture_output=True,
        text=True,
        timeout=10,
    )

    assert inspect_result.returncode == 0
    wheel_contents = inspect_result.stdout

    # Critical modules that MUST be in the wheel
    critical_modules = [
        "obra/__init__.py",
        "obra/cli.py",
        "obra/model_registry.py",
        "obra/api/__init__.py",
        "obra/auth/__init__.py",
        "obra/config/__init__.py",
        "obra/display/__init__.py",
        "obra/execution/__init__.py",
        "obra/hybrid/__init__.py",
        "obra/llm/__init__.py",
        "obra/security/__init__.py",  # The module that was missing in ISSUE-SIM-20251216-002
        "obra/security/prompt_sanitizer.py",
    ]

    missing_modules = []
    for module in critical_modules:
        if module not in wheel_contents:
            missing_modules.append(module)

    assert not missing_modules, (
        f"Critical modules missing from wheel: {missing_modules}\n"
        f"Check pyproject.toml packages list - all subpackages must be declared"
    )


def test_security_module_importable_from_wheel():
    """Verify obra.security can be imported from an installed wheel.

    This test actually installs the wheel in a temporary virtualenv and
    verifies that the security module can be imported successfully.

    This is the most realistic test - it simulates what end users experience.
    """
    # Get the obra package directory
    obra_dir = Path(__file__).parent.parent
    dist_dir = obra_dir / "dist"

    # Find the most recent wheel
    wheels = list(dist_dir.glob("obra-*.whl"))
    if not wheels:
        pytest.skip("No wheel found - run build first")

    wheel_path = max(wheels, key=lambda p: p.stat().st_mtime)

    # Create a temporary directory for testing installation
    with tempfile.TemporaryDirectory() as tmpdir:
        # Install the wheel in isolated mode (no system packages)
        install_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--target",
                tmpdir,
                "--no-deps",  # Don't install dependencies for this smoke test
                str(wheel_path),
            ],
            check=False, capture_output=True,
            text=True,
            timeout=30,
        )

        assert install_result.returncode == 0, (
            f"Wheel installation failed: {install_result.stderr}"
        )

        # Try to import the security module
        import_result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, {tmpdir!r}); "
                "from obra.security import PromptSanitizer; "
                "print('SUCCESS')",
            ],
            check=False, capture_output=True,
            text=True,
            timeout=10,
        )

        # BEFORE FIX: This will fail with ModuleNotFoundError
        # AFTER FIX: This will succeed and print "SUCCESS"
        assert import_result.returncode == 0, (
            f"Failed to import obra.security from installed wheel:\n"
            f"{import_result.stderr}\n"
            f"This indicates the security module is missing from the wheel distribution."
        )

        assert "SUCCESS" in import_result.stdout, (
            "Import succeeded but did not produce expected output"
        )
