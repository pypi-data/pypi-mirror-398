"""Structured output parser for LLM responses.

This module provides parsing and validation for LLM responses with
support for:
- JSON responses (with or without markdown code blocks)
- Hybrid format (JSON metadata + natural language content)
- Schema validation against defined response schemas
- Completion signal extraction

The parser handles malformed responses gracefully and provides
detailed validation feedback.

Example:
    >>> parser = OutputParser()
    >>> result = parser.parse(
    ...     response='{"plan_items": [...]}',
    ...     expected_format="json",
    ... )
    >>> if result.success:
    ...     print(result.data["plan_items"])

Related:
    - src/llm/structured_response_parser.py (CLI reference)
    - obra/llm/invoker.py
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CompletionSignal:
    """Extracted completion signal from agent response.

    Attributes:
        signal_type: One of TASK_COMPLETE, TASK_BLOCKED, TASK_PARTIAL, TASK_CLARIFY
        message: The accompanying message/summary
        next_action: Recommended orchestrator action
        confidence: Confidence in signal extraction (1.0 for explicit, <1.0 for inferred)
        is_inferred: Whether signal was inferred (True) or explicit (False)
    """

    signal_type: str
    message: str
    next_action: str
    confidence: float = 1.0
    is_inferred: bool = False


@dataclass
class ParsedOutput:
    """Result from parsing LLM output.

    Attributes:
        data: Parsed data (dict or string depending on format)
        metadata: Extracted metadata (for hybrid format)
        content: Natural language content (for hybrid format)
        success: Whether parsing succeeded
        errors: List of parsing/validation errors
        format_detected: Detected response format
        completion_signal: Extracted completion signal (if any)
    """

    data: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    content: str = ""
    success: bool = True
    errors: list[str] = field(default_factory=list)
    format_detected: str = "unknown"
    completion_signal: CompletionSignal | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "data": self.data,
            "metadata": self.metadata,
            "content": self.content,
            "success": self.success,
            "errors": self.errors,
            "format_detected": self.format_detected,
            "has_completion_signal": self.completion_signal is not None,
        }


class OutputParser:
    """Parser for structured LLM responses.

    Handles multiple response formats:
    - Pure JSON (with or without markdown code blocks)
    - Hybrid format (<METADATA>JSON</METADATA> + <CONTENT>text</CONTENT>)
    - Plain text

    Example:
        >>> parser = OutputParser()
        >>> result = parser.parse('{"items": [1, 2, 3]}', expected_format="json")
        >>> print(result.data)
        {'items': [1, 2, 3]}

    Thread-safety:
        Thread-safe (no mutable state).
    """

    # Patterns for extraction
    METADATA_PATTERN = re.compile(
        r"<METADATA>\s*(.*?)\s*</METADATA>",
        re.DOTALL | re.IGNORECASE,
    )
    CONTENT_PATTERN = re.compile(
        r"<CONTENT>\s*(.*?)\s*</CONTENT>",
        re.DOTALL | re.IGNORECASE,
    )
    JSON_CODE_BLOCK_PATTERN = re.compile(
        r"```(?:json)?\s*\n?(.*?)\n?```",
        re.DOTALL,
    )

    # Completion signal patterns
    SIGNAL_PATTERNS = {
        "TASK_COMPLETE": (
            re.compile(r"TASK_COMPLETE:\s*(.+)", re.MULTILINE),
            "proceed_to_next",
        ),
        "TASK_BLOCKED": (
            re.compile(r"TASK_BLOCKED:\s*(.+)", re.MULTILINE),
            "trigger_breakpoint",
        ),
        "TASK_PARTIAL": (
            re.compile(r"TASK_PARTIAL:\s*(.+)", re.MULTILINE),
            "continue_iteration",
        ),
        "TASK_CLARIFY": (
            re.compile(r"TASK_CLARIFY:\s*(.+)", re.MULTILINE),
            "prompt_user",
        ),
    }

    # Inference rules for signals
    INFERENCE_RULES = [
        {
            "pattern": re.compile(r"error|failed|cannot|blocked|unable", re.IGNORECASE),
            "signal": "TASK_BLOCKED",
            "action": "trigger_breakpoint",
            "confidence": 0.7,
        },
        {
            "pattern": re.compile(r"\?$", re.MULTILINE),
            "signal": "TASK_CLARIFY",
            "action": "prompt_user",
            "confidence": 0.6,
        },
        {
            "pattern": re.compile(r"still need|remaining|todo|incomplete", re.IGNORECASE),
            "signal": "TASK_PARTIAL",
            "action": "continue_iteration",
            "confidence": 0.6,
        },
        {
            "pattern": re.compile(r"completed|finished|done|implemented|added", re.IGNORECASE),
            "signal": "TASK_COMPLETE",
            "action": "proceed_to_next",
            "confidence": 0.5,
        },
    ]

    def parse(
        self,
        response: str,
        expected_format: str = "auto",
        schema: dict[str, Any] | None = None,
    ) -> ParsedOutput:
        """Parse LLM response.

        Args:
            response: Raw LLM response string
            expected_format: Expected format ("json", "hybrid", "text", "auto")
            schema: Optional schema for validation

        Returns:
            ParsedOutput with parsed data and metadata
        """
        if not response:
            return ParsedOutput(
                success=False,
                errors=["Empty response"],
                format_detected="empty",
            )

        # Detect format if auto
        if expected_format == "auto":
            expected_format = self._detect_format(response)

        # Parse based on format
        if expected_format == "json":
            return self._parse_json(response, schema)
        if expected_format == "hybrid":
            return self._parse_hybrid(response, schema)
        return self._parse_text(response)

    def _detect_format(self, response: str) -> str:
        """Detect response format.

        Args:
            response: Raw response string

        Returns:
            Detected format ("json", "hybrid", or "text")
        """
        # Check for hybrid format tags
        if self.METADATA_PATTERN.search(response):
            return "hybrid"

        # Check for JSON (direct or in code block)
        stripped = response.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            return "json"
        if self.JSON_CODE_BLOCK_PATTERN.search(response):
            return "json"

        return "text"

    def _parse_json(
        self,
        response: str,
        schema: dict[str, Any] | None = None,
    ) -> ParsedOutput:
        """Parse JSON response.

        Args:
            response: Raw response string
            schema: Optional schema for validation

        Returns:
            ParsedOutput with parsed JSON
        """
        errors: list[str] = []

        try:
            # Extract JSON from code block if present
            json_str = self._extract_json_string(response)

            # Parse JSON
            data = json.loads(json_str)

            # Validate against schema if provided
            if schema:
                validation_errors = self._validate_schema(data, schema)
                errors.extend(validation_errors)

            # Extract completion signal
            completion_signal = self._extract_completion_signal(response)

            return ParsedOutput(
                data=data,
                success=len(errors) == 0,
                errors=errors,
                format_detected="json",
                completion_signal=completion_signal,
            )

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            return ParsedOutput(
                success=False,
                errors=[f"JSON parse error: {e!s}"],
                format_detected="json",
                content=response,
            )

    def _parse_hybrid(
        self,
        response: str,
        schema: dict[str, Any] | None = None,
    ) -> ParsedOutput:
        """Parse hybrid format response.

        Args:
            response: Raw response string
            schema: Optional schema for validation

        Returns:
            ParsedOutput with metadata and content
        """
        errors: list[str] = []
        metadata: dict[str, Any] = {}
        content = ""

        # Extract metadata
        metadata_match = self.METADATA_PATTERN.search(response)
        if metadata_match:
            try:
                metadata = json.loads(metadata_match.group(1))
            except json.JSONDecodeError as e:
                errors.append(f"Metadata JSON parse error: {e!s}")
        else:
            errors.append("No <METADATA> tags found")

        # Extract content
        content_match = self.CONTENT_PATTERN.search(response)
        if content_match:
            content = content_match.group(1).strip()
        else:
            # Use response without metadata as content fallback
            content = self.METADATA_PATTERN.sub("", response).strip()

        # Validate metadata against schema
        if schema and metadata:
            validation_errors = self._validate_schema(metadata, schema)
            errors.extend(validation_errors)

        # Extract completion signal
        completion_signal = self._extract_completion_signal(response)

        return ParsedOutput(
            data=metadata,
            metadata=metadata,
            content=content,
            success=len(errors) == 0 or (metadata and content),
            errors=errors,
            format_detected="hybrid",
            completion_signal=completion_signal,
        )

    def _parse_text(self, response: str) -> ParsedOutput:
        """Parse plain text response.

        Args:
            response: Raw response string

        Returns:
            ParsedOutput with text content
        """
        # Extract completion signal
        completion_signal = self._extract_completion_signal(response)

        return ParsedOutput(
            data=response,
            content=response,
            success=True,
            format_detected="text",
            completion_signal=completion_signal,
        )

    def _extract_json_string(self, response: str) -> str:
        """Extract JSON string from response.

        Args:
            response: Raw response

        Returns:
            JSON string (without code block markers)
        """
        stripped = response.strip()

        # Check for code block
        code_block_match = self.JSON_CODE_BLOCK_PATTERN.search(response)
        if code_block_match:
            return code_block_match.group(1).strip()

        # Remove leading ```json and trailing ``` if present
        if stripped.startswith("```"):
            lines = stripped.split("\n")
            start = 1 if lines[0].startswith("```") else 0
            end = len(lines) - 1 if lines[-1] == "```" else len(lines)
            return "\n".join(lines[start:end])

        return stripped

    def _validate_schema(
        self,
        data: Any,
        schema: dict[str, Any],
    ) -> list[str]:
        """Validate data against schema.

        Args:
            data: Data to validate
            schema: Schema definition

        Returns:
            List of validation errors
        """
        errors: list[str] = []

        if not isinstance(data, dict):
            errors.append(f"Expected dict, got {type(data).__name__}")
            return errors

        # Check required fields
        required_fields = schema.get("required_fields", [])
        for field_spec in required_fields:
            if isinstance(field_spec, str):
                field_name = field_spec
                field_type = None
            else:
                field_name = field_spec.get("name")
                field_type = field_spec.get("type")

            if field_name not in data:
                errors.append(f"Missing required field: {field_name}")
                continue

            # Type validation
            if field_type:
                type_error = self._validate_type(
                    data[field_name],
                    field_type,
                    field_name,
                )
                if type_error:
                    errors.append(type_error)

        return errors

    def _validate_type(
        self,
        value: Any,
        expected_type: str,
        field_name: str,
    ) -> str | None:
        """Validate field type.

        Args:
            value: Value to validate
            expected_type: Expected type string
            field_name: Field name for error message

        Returns:
            Error message or None
        """
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected_python_type = type_map.get(expected_type)
        if expected_python_type is None:
            return None

        if not isinstance(value, expected_python_type):
            return f"Field '{field_name}' expected {expected_type}, got {type(value).__name__}"

        return None

    def _extract_completion_signal(self, response: str) -> CompletionSignal | None:
        """Extract completion signal from response.

        First looks for explicit signal prefixes, then infers from content.

        Args:
            response: Response text

        Returns:
            CompletionSignal or None
        """
        if not response:
            return None

        # Try explicit signal extraction
        for signal_type, (pattern, next_action) in self.SIGNAL_PATTERNS.items():
            match = pattern.search(response)
            if match:
                return CompletionSignal(
                    signal_type=signal_type,
                    message=match.group(1).strip(),
                    next_action=next_action,
                    confidence=1.0,
                    is_inferred=False,
                )

        # Fallback to inference
        return self._infer_signal(response)

    def _infer_signal(self, response: str) -> CompletionSignal | None:
        """Infer completion signal from response content.

        Args:
            response: Response text

        Returns:
            CompletionSignal with lower confidence, or None
        """
        if not response:
            return None

        best_match = None
        best_confidence = 0.0

        for rule in self.INFERENCE_RULES:
            if rule["pattern"].search(response):
                if rule["confidence"] > best_confidence:
                    best_match = rule
                    best_confidence = rule["confidence"]

        if best_match:
            # Extract last sentence as message
            sentences = response.strip().split(".")
            message = sentences[-1].strip() if sentences else response[:100]

            return CompletionSignal(
                signal_type=best_match["signal"],
                message=message,
                next_action=best_match["action"],
                confidence=best_match["confidence"],
                is_inferred=True,
            )

        # Default to TASK_COMPLETE with low confidence
        return CompletionSignal(
            signal_type="TASK_COMPLETE",
            message="(No explicit signal found)",
            next_action="proceed_to_next",
            confidence=0.3,
            is_inferred=True,
        )

    @staticmethod
    def get_signal_instructions() -> str:
        """Get instructions template for completion signals.

        Returns:
            String with signal protocol instructions for prompts
        """
        return """
## Response Protocol
End your response with one of these status indicators:

TASK_COMPLETE: <brief summary of what was accomplished>
TASK_BLOCKED: <what's blocking progress and why>
TASK_PARTIAL: <what was done and what remains>
TASK_CLARIFY: <specific question needing an answer>

Example: TASK_COMPLETE: Implemented user authentication with JWT tokens
""".strip()


__all__ = [
    "CompletionSignal",
    "OutputParser",
    "ParsedOutput",
]
