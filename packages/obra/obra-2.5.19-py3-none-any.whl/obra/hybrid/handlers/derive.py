"""Derive handler for Hybrid Orchestrator.

This module handles the DERIVE action from the server. It takes an objective
and derives an implementation plan using the local LLM invocation.

The derivation process:
    1. Receive DeriveRequest with objective and context
    2. Gather local project context (files, structure, etc.)
    3. Invoke LLM to generate plan
    4. Parse structured output into plan items
    5. Return DerivedPlan to report to server

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md Section 1
    - obra/api/protocol.py
    - obra/hybrid/orchestrator.py
"""

import json
import logging
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from obra.api.protocol import DeriveRequest
from obra.display import print_info
from obra.hybrid.json_utils import extract_json_payload, unwrap_claude_cli_json
from obra.hybrid.prompt_enricher import PromptEnricher
from obra.llm.cli_runner import invoke_llm_via_cli
from obra.model_registry import get_default_model, validate_model

logger = logging.getLogger(__name__)


class DeriveHandler:
    """Handler for DERIVE action.

    Derives an implementation plan from the objective using LLM.
    The plan is structured as a list of plan items (tasks/stories).

    ## Architecture Context (ADR-027)

    This handler implements the two-tier prompting architecture where:
    - **Server (Tier 1)**: Generates strategic base prompts with CLIENT_CONTEXT_MARKER
    - **Client (Tier 2)**: Enriches base prompts with local tactical context

    **Implementation Flow**:
    1. Server sends DeriveRequest with base_prompt containing strategic instructions
    2. Client enriches base_prompt via PromptEnricher (adds file structure, git log)
    3. Client invokes LLM with enriched prompt locally
    4. Client reports plan items and raw response back to server

    ## IP Protection

    Strategic prompt engineering (system patterns, quality standards) stays on server.
    This protects Obra's proprietary prompt engineering IP from client-side inspection.

    ## Privacy Protection

    Tactical context (file contents, git messages, errors) never sent to server.
    Only LLM response summary (plan items) is transmitted.

    See: docs/decisions/ADR-027-two-tier-prompting-architecture.md

    Example:
        >>> handler = DeriveHandler(Path("/path/to/project"))
        >>> request = DeriveRequest(objective="Add user authentication")
        >>> result = handler.handle(request)
        >>> print(result["plan_items"])
    """

    def __init__(
        self,
        working_dir: Path,
        on_stream: Callable[[str, str], None] | None = None,
        llm_config: dict[str, Any] | None = None,
        log_event: Callable[..., None] | None = None,
    ) -> None:
        """Initialize DeriveHandler.

        Args:
            working_dir: Working directory for file access
            on_stream: Optional callback for LLM streaming chunks (S3.T6)
            llm_config: Optional LLM configuration (S4.T2)
            log_event: Optional logger for hybrid events (ISSUE-OBS-002)
        """
        self._working_dir = working_dir
        self._on_stream = on_stream
        self._llm_config = llm_config or {}
        self._log_event = log_event

    def handle(self, request: DeriveRequest) -> dict[str, Any]:
        """Handle DERIVE action.

        Args:
            request: DeriveRequest from server with base_prompt

        Returns:
            Dict with plan_items and raw_response

        Raises:
            ValueError: If request.base_prompt is None (server must provide base_prompt)
        """
        logger.info(f"Deriving plan for: {request.objective[:50]}...")
        print_info(f"Deriving plan for: {request.objective[:50]}...")

        # Validate base_prompt (server-side prompting required)
        if request.base_prompt is None:
            error_msg = "DeriveRequest.base_prompt is None. Server must provide base prompt (ADR-027)."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Enrich base prompt with local tactical context
        enricher = PromptEnricher(self._working_dir)
        enriched_prompt = enricher.enrich(request.base_prompt)

        provider, model, thinking_level = self._resolve_llm_config(request.llm_provider)

        # Invoke LLM with enriched prompt
        raw_response = self._invoke_llm(
            enriched_prompt,
            provider=provider,
            model=model,
            thinking_level=thinking_level,
        )

        # Parse response into plan items
        plan_items, parse_info = self._parse_plan(raw_response)
        self._log_parse_event(
            action="derive",
            provider=provider,
            model=model,
            parse_info=parse_info,
        )

        if self._should_retry_on_parse_failure(provider, model, parse_info):
            retry_prompt = self._build_retry_prompt(enriched_prompt)
            self._log_retry_event(
                action="derive",
                provider=provider,
                model=model,
                attempt=1,
                reason=parse_info.get("status", "unknown"),
            )
            raw_response = self._invoke_llm(
                retry_prompt,
                provider=provider,
                model=model,
                thinking_level=thinking_level,
            )
            plan_items, parse_info = self._parse_plan(raw_response)
            parse_info["retried"] = True
            self._log_parse_event(
                action="derive",
                provider=provider,
                model=model,
                parse_info=parse_info,
            )

        logger.info(f"Derived {len(plan_items)} plan items")
        print_info(f"Derived {len(plan_items)} plan items")

        return {
            "plan_items": plan_items,
            "raw_response": raw_response,
        }

    def _invoke_llm(
        self,
        prompt: str,
        *,
        provider: str,
        model: str,
        thinking_level: str,
    ) -> str:
        """Invoke LLM to generate plan.

        Args:
            prompt: Derivation prompt
            provider: LLM provider name
            model: LLM model name
            thinking_level: LLM thinking level

        Returns:
            Raw LLM response
        """
        logger.debug(f"Invoking LLM via CLI: provider={provider} model={model} thinking={thinking_level}")

        def _stream(chunk: str) -> None:
            if self._on_stream:
                self._on_stream("llm_streaming", chunk)

        try:
            schema_path = None
            if provider == "openai":
                schema = {
                    "type": "object",
                    "properties": {
                        "plan_items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "item_type": {"type": "string"},
                                    "title": {"type": "string"},
                                    "description": {"type": "string"},
                                    "acceptance_criteria": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "dependencies": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "required": [
                                    "id",
                                    "item_type",
                                    "title",
                                    "description",
                                    "acceptance_criteria",
                                    "dependencies",
                                ],
                            },
                        }
                    },
                    "required": ["plan_items"],
                }
                with tempfile.NamedTemporaryFile(
                    mode="w+",
                    delete=False,
                    encoding="utf-8",
                ) as schema_file:
                    json.dump(schema, schema_file)
                    schema_path = Path(schema_file.name)
            try:
                return invoke_llm_via_cli(
                    prompt=prompt,
                    cwd=self._working_dir,
                    provider=provider,
                    model=model,
                    thinking_level=thinking_level,
                    on_stream=_stream if self._on_stream else None,
                    output_schema=schema_path,
                )
            finally:
                if schema_path:
                    schema_path.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            return json.dumps(
                {
                    "plan_items": [
                        {
                            "id": "ERROR",
                            "item_type": "task",
                            "title": "LLM Error",
                            "description": f"LLM invocation failed: {e!s}",
                            "acceptance_criteria": [],
                            "dependencies": [],
                        }
                    ]
                }
            )

    def _parse_plan(self, raw_response: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Parse LLM response into plan items.

        Args:
            raw_response: Raw LLM response

        Returns:
            List of plan item dictionaries

        Note:
            ISSUE-SAAS-018 fix: Now tries multiple key names that LLMs commonly use
            (plan_items, tasks, items, plan, stories) before falling back to
            wrapping as single item.
        """
        parse_info = {
            "status": "strict_json",
            "response_length": len(raw_response),
            "used_extraction": False,
        }
        try:
            # Try to extract JSON from response
            # Handle case where response might have markdown code blocks
            response = raw_response.strip()

            if response.startswith("```"):
                # Extract from code block
                lines = response.split("\n")
                start = 1 if lines[0].startswith("```") else 0
                end = len(lines) - 1 if lines[-1] == "```" else len(lines)
                response = "\n".join(lines[start:end])

            # Parse JSON
            try:
                data = json.loads(response)
            except json.JSONDecodeError as e:
                candidate = extract_json_payload(raw_response)
                if candidate and candidate != response:
                    parse_info["status"] = "tolerant_json"
                    parse_info["used_extraction"] = True
                    data = json.loads(candidate)
                elif raw_response.strip():
                    logger.warning("Non-JSON plan response received; coercing to single task.")
                    parse_info["status"] = "coerced_text"
                    return self._coerce_text_plan(raw_response), parse_info
                else:
                    parse_info["status"] = "parse_error_fallback"
                    parse_info["error"] = str(e)
                    return self._create_parse_error_fallback(raw_response, e), parse_info

            # ISSUE-SAAS-030 FIX: Handle Claude CLI JSON wrapper format
            # When --output-format json is used, Claude CLI wraps the response
            data, was_unwrapped = unwrap_claude_cli_json(data)
            if was_unwrapped:
                logger.debug("Detected Claude CLI JSON wrapper, extracted result field")
                parse_info["unwrapped_cli_json"] = True
                # If unwrap returned a string (not JSON), coerce to single task
                if isinstance(data, str):
                    logger.warning("Claude CLI result is not valid JSON; coercing to single task.")
                    parse_info["status"] = "coerced_text"
                    return self._coerce_text_plan(data), parse_info

            # ISSUE-SAAS-018: Try multiple common key names LLMs might use
            items = None
            if isinstance(data, dict):
                # Try common key names in order of preference
                for key in ["plan_items", "tasks", "items", "plan", "stories"]:
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        if key != "plan_items":
                            logger.info(f"Found plan items under '{key}' key instead of 'plan_items'")
                        break

                if items is None:
                    logger.info("Unexpected response format, wrapping as single item")
                    items = [data]
            elif isinstance(data, list):
                items = data
            else:
                logger.warning("Unexpected response format (not dict or list), wrapping as single item")
                items = [{"description": str(data)}]

            # Validate and normalize items
            normalized = []
            for i, item in enumerate(items):
                normalized_item = {
                    "id": item.get("id", f"T{i + 1}"),
                    "item_type": item.get("item_type", "task"),
                    "title": item.get("title", "Untitled"),
                    "description": item.get("description", ""),
                    "acceptance_criteria": item.get("acceptance_criteria", []),
                    "dependencies": item.get("dependencies", []),
                }
                normalized.append(normalized_item)

            return normalized, parse_info

        except json.JSONDecodeError as e:
            parse_info["status"] = "parse_error_fallback"
            parse_info["error"] = str(e)
            return self._create_parse_error_fallback(raw_response, e), parse_info

    def _coerce_text_plan(self, raw_response: str) -> list[dict[str, Any]]:
        """Coerce a non-JSON response into a minimal plan item."""
        trimmed = raw_response.strip()
        return [
            {
                "id": "T1",
                "item_type": "task",
                "title": "Complete objective from non-JSON plan",
                "description": trimmed,
                "acceptance_criteria": [
                    "Objective is completed with a concrete deliverable",
                ],
                "dependencies": [],
            }
        ]

    def _create_parse_error_fallback(
        self, raw_response: str, error: json.JSONDecodeError
    ) -> list[dict[str, Any]]:
        """Create diagnostic fallback plan when JSON parsing fails.

        Args:
            raw_response: The raw response that failed to parse
            error: The JSONDecodeError exception

        Returns:
            List containing single diagnostic task with actionable information
        """
        # Analyze the response to provide helpful diagnostics
        response_length = len(raw_response)
        trimmed = raw_response.strip()
        is_empty = response_length == 0 or len(trimmed) == 0

        # Extract first few characters for preview (safely handle empty)
        preview = trimmed[:100] if trimmed else "(empty response)"
        if len(trimmed) > 100:
            preview += "..."

        # Build diagnostic description
        description_parts = [
            "**LLM Response Parse Error**",
            "",
            f"**Error**: {error.msg}",
            f"**Position**: Line {error.lineno}, Column {error.colno}",
            "",
        ]

        if is_empty:
            description_parts.extend([
                "**Issue**: The LLM returned an empty response.",
                "",
                "**Possible Causes**:",
                "- LLM CLI failed silently without error code",
                "- Response was filtered or truncated",
                "- Timeout or connection issue during streaming",
                "",
                "**Recommended Actions**:",
                "1. Check LLM provider logs for errors",
                "2. Verify LLM CLI is properly configured (`obra config`)",
                "3. Test LLM connection directly (e.g., `claude --version`)",
                "4. Try again with `--verbose` flag for detailed output",
            ])
        else:
            description_parts.extend([
                "**Response Preview**:",
                "```",
                f"{preview}",
                "```",
                "",
                f"**Response Length**: {response_length} characters",
                "",
                "**Possible Causes**:",
                "- LLM returned natural language instead of JSON",
                "- Response format changed or is malformed",
                "- Code block markers (```) not properly removed",
                "",
                "**Recommended Actions**:",
                "1. Review the raw response in session logs",
                "2. Check if LLM is using correct output format",
                "3. Try with different LLM provider or model",
                "4. Report issue if this persists",
            ])

        description = "\n".join(description_parts)

        logger.error(
            f"Failed to parse plan JSON: {error}. "
            f"Response length: {response_length}, "
            f"Is empty: {is_empty}, "
            f"Preview: {preview}"
        )

        # Return diagnostic fallback item
        return [
            {
                "id": "PARSE_ERROR",
                "item_type": "task",
                "title": "LLM Response Parse Error - Manual Review Required",
                "description": description,
                "acceptance_criteria": [
                    "Investigate root cause of parse error",
                    "Verify LLM configuration is correct",
                    "Retry derivation with corrected setup",
                ],
                "dependencies": [],
            }
        ]

    def _resolve_llm_config(self, provider: str) -> tuple[str, str, str]:
        resolved_provider = self._llm_config.get("provider", provider)
        model = self._llm_config.get("model", "default")
        thinking_level = self._llm_config.get("thinking_level", "medium")
        return resolved_provider, model, thinking_level

    def _normalize_model(self, provider: str, model: str) -> str | None:
        if not model or model in ("default", "auto"):
            return get_default_model(provider)
        return model

    def _should_retry_on_parse_failure(
        self,
        provider: str,
        model: str,
        parse_info: dict[str, Any],
    ) -> bool:
        if parse_info.get("status") not in ("coerced_text", "parse_error_fallback"):
            return False

        if not self._llm_config.get("parse_retry_enabled", True):
            return False

        parse_retry_providers = self._llm_config.get("parse_retry_providers")
        if parse_retry_providers is None:
            parse_retry_providers = ["openai"]
        if isinstance(parse_retry_providers, str):
            parse_retry_providers = [parse_retry_providers]
        if provider not in parse_retry_providers:
            return False

        parse_retry_models = self._llm_config.get("parse_retry_models")
        if parse_retry_models:
            if isinstance(parse_retry_models, str):
                parse_retry_models = [parse_retry_models]
            normalized_model = self._normalize_model(provider, model)
            if not normalized_model:
                return False
            if normalized_model not in parse_retry_models:
                return False

            validation = validate_model(provider, normalized_model)
            if not validation.valid:
                logger.warning("Parse retry model rejected by registry: %s", validation.error)
                return False

        return True

    def _build_retry_prompt(self, prompt: str) -> str:
        return (
            f"{prompt}\n\n"
            "Return only valid JSON for the response schema. "
            "Do not include prose, markdown, or code fences."
        )

    def _log_parse_event(
        self,
        *,
        action: str,
        provider: str,
        model: str,
        parse_info: dict[str, Any],
    ) -> None:
        if not self._log_event:
            return
        try:
            self._log_event(
                "hybrid_parse_result",
                action=action,
                provider=provider,
                model=model,
                status=parse_info.get("status"),
                used_extraction=parse_info.get("used_extraction", False),
                retried=parse_info.get("retried", False),
                response_length=parse_info.get("response_length", 0),
            )
        except Exception as e:
            logger.debug("Failed to log hybrid parse event: %s", e)

    def _log_retry_event(
        self,
        *,
        action: str,
        provider: str,
        model: str,
        attempt: int,
        reason: str,
    ) -> None:
        if not self._log_event:
            return
        try:
            self._log_event(
                "hybrid_parse_retry",
                action=action,
                provider=provider,
                model=model,
                attempt=attempt,
                reason=reason,
            )
        except Exception as e:
            logger.debug("Failed to log hybrid retry event: %s", e)


__all__ = ["DeriveHandler"]
