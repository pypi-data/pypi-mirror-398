"""Utilities for extracting JSON payloads from LLM responses."""

from __future__ import annotations

import json
import re
from typing import Any, Optional


def unwrap_claude_cli_json(data: dict[str, Any]) -> tuple[Any, bool]:
    """Unwrap Claude CLI JSON wrapper format.

    When Claude CLI is invoked with --output-format json, it returns a wrapper:
    {"type": "result", "result": "...", ...}

    This function extracts the actual LLM response from the "result" field.

    Args:
        data: Parsed JSON data that may be a Claude CLI wrapper

    Returns:
        Tuple of (unwrapped_data, was_wrapped) where:
        - unwrapped_data: The actual LLM response (parsed if JSON, or string)
        - was_wrapped: True if data was a Claude CLI wrapper

    ISSUE-SAAS-030: Fixes derivation returning empty plan items because
    the wrapper JSON was being treated as the plan instead of its result field.
    """
    if not isinstance(data, dict):
        return data, False

    # Check for Claude CLI wrapper signature
    if data.get("type") == "result" and "result" in data:
        result_content = data["result"]

        if isinstance(result_content, str):
            result_content = result_content.strip()
            # Remove markdown code blocks if present
            if result_content.startswith("```"):
                lines = result_content.split("\n")
                start = 1 if lines[0].startswith("```") else 0
                end = len(lines) - 1 if lines[-1] == "```" else len(lines)
                result_content = "\n".join(lines[start:end])
            # Try to parse as JSON
            try:
                return json.loads(result_content), True
            except json.JSONDecodeError:
                # Return as-is if not valid JSON
                return result_content, True

        elif isinstance(result_content, (dict, list)):
            return result_content, True

    return data, False


def extract_json_payload(text: str) -> Optional[str]:
    """Extract a JSON object/array from a mixed response.

    Returns the first plausible JSON payload as a string, or None if not found.
    """
    trimmed = text.strip()
    if not trimmed:
        return None

    code_block = re.search(r"```(?:json)?\s*(.*?)```", trimmed, re.DOTALL)
    if code_block:
        candidate = code_block.group(1).strip()
        if candidate:
            return candidate

    for opener, closer in (("{", "}"), ("[", "]")):
        start = trimmed.find(opener)
        end = trimmed.rfind(closer)
        if start != -1 and end != -1 and end > start:
            return trimmed[start : end + 1].strip()

    return None
