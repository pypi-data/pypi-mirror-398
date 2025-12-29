"""Unified plan validator using Pydantic schema validation.

This module provides the new generation plan validator that replaces
the multi-layer patch stack with strict Pydantic schema validation.

Architecture:
    - Format detection: Automatic JSON/YAML detection
    - Schema validation: Pydantic MachinePlanSchema
    - Error formatting: User-friendly Pydantic error messages

Design Principles:
    - Single source of truth: MachinePlanSchema defines valid structure
    - Clear error messages: Convert Pydantic errors to actionable guidance
    - Format agnostic: Support both JSON (preferred) and YAML

Related:
    - docs/design/briefs/PLAN_VALIDATION_ARCHITECTURE_REDESIGN_BRIEF.md
    - docs/guides/workflows/plan-file-workflow.md
    - obra/schemas/plan_schema.py (schema definitions)

Example:
    >>> from obra.validation.plan_validator import PlanValidator
    >>> validator = PlanValidator()
    >>> plan = validator.validate_file("/path/to/MACHINE_PLAN.json")
    >>> print(f"Valid plan: {plan.work_id}")
"""

import json
import logging
from pathlib import Path
from typing import Literal

try:
    import yaml
except ImportError:
    yaml = None  # Optional dependency

from pydantic import ValidationError

from obra.schemas.plan_schema import MachinePlanSchema
from obra.validation.exceptions import YamlValidationError

logger = logging.getLogger(__name__)


class PlanValidationError(Exception):
    """Exception raised when plan validation fails.

    This exception provides detailed error context including:
    - File path where the error occurred
    - Format detected (JSON or YAML)
    - User-friendly error messages
    - Line numbers and field context
    - Actionable suggestions for fixing errors

    Attributes:
        file_path: Path to the plan file that failed validation
        format: Detected file format ('json' or 'yaml')
        errors: List of formatted error messages
        raw_exception: Original Pydantic ValidationError (for debugging)

    Example:
        >>> try:
        ...     validator.validate_file("plan.yaml")
        ... except PlanValidationError as e:
        ...     print(f"Validation failed for {e.file_path}")
        ...     for error in e.errors:
        ...         print(f"  - {error}")
    """

    def __init__(
        self,
        file_path: str,
        format: str,
        errors: list[str],
        raw_exception: Exception,
    ) -> None:
        """Initialize PlanValidationError.

        Args:
            file_path: Path to the plan file
            format: Detected file format ('json' or 'yaml')
            errors: List of formatted error messages
            raw_exception: Original exception (for debugging)
        """
        self.file_path = file_path
        self.format = format
        self.errors = errors
        self.raw_exception = raw_exception

        # Build comprehensive exception message
        message = self._build_message()
        super().__init__(message)

    def _build_message(self) -> str:
        """Build comprehensive error message with all context.

        Returns:
            Formatted error message with file path, format, errors, and suggestions
        """
        lines = []

        # Header
        lines.append("Plan validation failed")
        lines.append("")

        # File and format
        lines.append(f"File: {self.file_path}")
        lines.append(f"Format: {self.format.upper()}")
        lines.append("")

        # Errors
        lines.append("Errors:")
        for error in self.errors:
            lines.append(f"  {error}")
        lines.append("")

        # Suggestions
        lines.append("Next steps:")
        lines.append("  1. Fix the validation errors in the file and retry")
        lines.append("  2. See docs/guides/migration/plan-validation-v2-migration.md for migration help")
        lines.append("  3. Validate with: obra validate-plan <file>")
        lines.append("")

        return "\n".join(lines)


class PlanValidator:
    """Unified plan validator using Pydantic schema validation.

    Validates MACHINE_PLAN files (JSON or YAML format) against the
    MachinePlanSchema. Provides clear error messages with line numbers
    and actionable suggestions.

    This validator replaces the legacy multi-layer validator
    (src.validation.plan_file_validator.PlanFileValidator) with a
    single Pydantic-based approach.

    Example:
        >>> validator = PlanValidator()
        >>> plan = validator.validate_file("MACHINE_PLAN.json")
        >>> print(f"Work ID: {plan.work_id}")
        >>> print(f"Stories: {len(plan.stories)}")
    """

    def __init__(self) -> None:
        """Initialize PlanValidator."""

    def validate_file(self, file_path: str) -> MachinePlanSchema:
        """Validate a plan file and return validated schema.

        Args:
            file_path: Path to MACHINE_PLAN.json or .yaml file

        Returns:
            Validated MachinePlanSchema instance

        Raises:
            PlanValidationError: If validation fails with detailed error context
            FileNotFoundError: If file does not exist
            ValueError: If file format cannot be detected or parsed

        Example:
            >>> validator = PlanValidator()
            >>> plan = validator.validate_file("docs/development/FEAT-001_MACHINE_PLAN.json")
            >>> assert plan.work_id == "FEAT-001"
        """
        # Check file exists
        path = Path(file_path)
        if not path.exists():
            raise YamlValidationError(
                file_path=file_path,
                error_message=f"File not found: {file_path}",
                line_number=None,
                suggestions=["Check the file path and try again."],
                auto_fix_attempted=False,
            )

        # Detect format
        format = self._detect_format(file_path)
        logger.debug(f"Detected format: {format} for file: {file_path}")

        # Parse file
        try:
            data = self._parse_file(file_path, format)
        except Exception as e:
            if format == "yaml" and yaml is not None and isinstance(e, yaml.YAMLError):
                raise self._build_yaml_validation_error(file_path, e) from e
            raise ValueError(
                f"Failed to parse {format.upper()} file: {file_path}. "
                f"Error: {e}"
            )

        # Validate against schema
        try:
            plan = MachinePlanSchema.model_validate(data)
            logger.debug(f"Successfully validated plan: {plan.work_id}")
            return plan
        except ValidationError as e:
            # Format errors into user-friendly messages
            errors = self._format_pydantic_errors(e)
            raise PlanValidationError(
                file_path=file_path,
                format=format,
                errors=errors,
                raw_exception=e,
            )

    def _detect_format(self, file_path: str) -> Literal["json", "yaml"]:
        """Detect file format based on extension.

        Args:
            file_path: Path to the plan file

        Returns:
            'json' or 'yaml'

        Raises:
            ValueError: If format cannot be determined

        Example:
            >>> validator = PlanValidator()
            >>> validator._detect_format("plan.json")
            'json'
            >>> validator._detect_format("plan.yaml")
            'yaml'
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".json":
            return "json"
        if suffix in [".yaml", ".yml"]:
            return "yaml"
        raise ValueError(
            f"Unknown file format: {suffix}. "
            f"Expected .json, .yaml, or .yml"
        )

    def _parse_file(self, file_path: str, format: str) -> dict:
        """Parse file contents based on detected format.

        Args:
            file_path: Path to the plan file
            format: Detected format ('json' or 'yaml')

        Returns:
            Parsed dictionary

        Raises:
            ValueError: If format is not supported or parsing fails
        """
        if format == "json":
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        elif format == "yaml":
            if yaml is None:
                raise ValueError(
                    "PyYAML library not available. Install with: pip install pyyaml"
                )
            with open(file_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _build_yaml_validation_error(
        self, file_path: str, exc: Exception
    ) -> YamlValidationError:
        """Build a YamlValidationError with context for YAML parse failures."""
        line_number = None
        error_message = str(exc)

        problem_mark = getattr(exc, "problem_mark", None)
        if problem_mark is not None and getattr(problem_mark, "line", None) is not None:
            line_number = problem_mark.line + 1

        suggestions = self._suggest_yaml_fixes(error_message)

        return YamlValidationError(
            file_path=file_path,
            error_message=error_message,
            line_number=line_number,
            suggestions=suggestions,
            auto_fix_attempted=True,
        )

    def _suggest_yaml_fixes(self, error_message: str) -> list[str]:
        """Generate basic YAML fix suggestions from a parse error message."""
        suggestions = []
        lowered = error_message.lower()

        if "indent" in lowered or "block" in lowered:
            suggestions.append("Check indentation for list items and nested blocks.")
        if "expected ':'" in lowered or "could not find expected ':'" in lowered:
            suggestions.append("Ensure every key is followed by a colon and value.")
        if "cannot start any token" in lowered or "found character" in lowered:
            suggestions.append("Wrap special characters in quotes.")

        if not suggestions:
            suggestions.append("Validate YAML syntax and indentation.")

        return suggestions

    def _format_pydantic_errors(self, exc: ValidationError) -> list[str]:
        """Format Pydantic validation errors into user-friendly messages.

        Converts Pydantic's technical error format into actionable guidance
        with field context and line numbers where possible.

        Args:
            exc: Pydantic ValidationError

        Returns:
            List of formatted error messages

        Example:
            >>> errors = validator._format_pydantic_errors(validation_error)
            >>> for error in errors:
            ...     print(error)
            [work_id] String should match pattern '^[A-Z]+-[A-Z-]+-\\d{3}$'
            [stories.0.tasks.0.status] Input should be 'pending', 'in_progress', 'completed', or 'blocked'
        """
        formatted_errors = []

        for error in exc.errors():
            # Build field path (e.g., "stories.0.tasks.0.status")
            location = ".".join(str(loc) for loc in error["loc"])

            # Get error type and message
            error_type = error["type"]
            error_msg = error["msg"]

            # Build formatted message
            if error_type == "missing":
                formatted = f"[{location}] Field required"
            elif error_type == "string_pattern_mismatch":
                pattern = error.get("ctx", {}).get("pattern", "")
                formatted = f"[{location}] String should match pattern '{pattern}'"
            elif error_type == "literal_error":
                expected = error.get("ctx", {}).get("expected", "")
                formatted = f"[{location}] {error_msg}"
            elif error_type == "list_type":
                formatted = f"[{location}] {error_msg}"
            else:
                formatted = f"[{location}] {error_msg}"

            # Add checkbox pattern detection for common YAML issue
            if "completion_checklist" in location and "list" in error_msg.lower():
                formatted += (
                    " | YAML checkbox patterns like '- [ ] Item' must be quoted: "
                    "'- \"[ ] Item\"'. See docs/guides/migration/plan-validation-v2-migration.md"
                )

            formatted_errors.append(formatted)

        return formatted_errors


# Convenience exports
__all__ = ["PlanValidationError", "PlanValidator"]
