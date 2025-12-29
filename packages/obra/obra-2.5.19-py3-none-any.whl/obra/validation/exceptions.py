"""Custom exceptions for YAML validation in the obra package.

This module provides validation exceptions for the obra CLI client.
"""

from typing import List, Optional


class YamlValidationError(Exception):
    """Exception raised when YAML validation fails.

    Attributes:
        file_path: Path to the YAML file that failed validation
        error_message: Descriptive error message
        line_number: Line number where error occurred (None if not available)
        suggestions: List of actionable suggestions for fixing the error
        auto_fix_attempted: Whether auto-sanitization was attempted before failure
    """

    def __init__(
        self,
        file_path: str,
        error_message: str,
        line_number: Optional[int] = None,
        suggestions: Optional[List[str]] = None,
        auto_fix_attempted: bool = False,
    ) -> None:
        self.file_path = file_path
        self.error_message = error_message
        self.line_number = line_number
        self.suggestions = suggestions or []
        self.auto_fix_attempted = auto_fix_attempted

        message = self._build_message()
        super().__init__(message)

    def _build_message(self) -> str:
        """Build comprehensive error message with all context."""
        lines = []
        lines.append("YAML validation failed")
        lines.append("")
        lines.append(f"File: {self.file_path}")
        if self.line_number is not None:
            lines.append(f"Line: {self.line_number}")
        lines.append("")
        lines.append("Error:")
        lines.append(f"  {self.error_message}")
        lines.append("")

        if self.auto_fix_attempted:
            lines.append("Auto-fix was attempted but could not resolve the issue.")
            lines.append("")

        if self.suggestions:
            lines.append("Suggestions:")
            for suggestion in self.suggestions:
                lines.append(f"  - {suggestion}")
            lines.append("")

        lines.append("Next steps:")
        lines.append("  1. Fix the YAML syntax error(s) in the file and retry")
        lines.append("  2. OR provide a natural language prompt with full context instead of YAML")

        return "\n".join(lines)


__all__ = ["YamlValidationError"]
