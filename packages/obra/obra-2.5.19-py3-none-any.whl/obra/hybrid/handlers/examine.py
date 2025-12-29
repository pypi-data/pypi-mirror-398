"""Examine handler for Hybrid Orchestrator.

This module handles the EXAMINE action from the server. It examines the current
plan using LLM to identify issues that need to be addressed.

The examination process:
    1. Receive ExamineRequest with plan to examine
    2. Build examination prompt with IP-protected criteria from server
    3. Invoke LLM with extended thinking if required
    4. Parse structured issues from response
    5. Return ExaminationReport to report to server

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

from obra.api.protocol import ExamineRequest
from obra.display import print_info
from obra.hybrid.json_utils import extract_json_payload, unwrap_claude_cli_json
from obra.hybrid.prompt_enricher import PromptEnricher
from obra.llm.cli_runner import invoke_llm_via_cli
from obra.model_registry import get_default_model, validate_model

logger = logging.getLogger(__name__)


class ExamineHandler:
    """Handler for EXAMINE action.

    Examines the current plan using LLM to identify issues.
    Issues are categorized and assigned severity levels.

    ## Architecture Context (ADR-027)

    This handler implements the two-tier prompting architecture where:
    - **Server (Tier 1)**: Generates strategic base prompts with examination criteria
    - **Client (Tier 2)**: Enriches base prompts with local tactical context

    **Implementation Flow**:
    1. Server sends ExamineRequest with base_prompt containing examination criteria
    2. Client enriches base_prompt via PromptEnricher (adds file structure, git log)
    3. Client invokes LLM with enriched prompt locally
    4. Client reports issues back to server for validation

    ## IP Protection

    Strategic examination criteria (quality standards, issue patterns) stay on server.
    This protects Obra's proprietary quality assessment IP from client-side inspection.

    ## Privacy Protection

    Tactical context (file contents, git messages, errors) never sent to server.
    Only LLM examination results (issues summary) is transmitted.

    See: docs/decisions/ADR-027-two-tier-prompting-architecture.md

    Example:
        >>> handler = ExamineHandler(Path("/path/to/project"))
        >>> request = ExamineRequest(
        ...     plan_version_id="v1",
        ...     plan_items=[{"id": "T1", "title": "Task 1", ...}]
        ... )
        >>> result = handler.handle(request)
        >>> print(result["issues"])
    """

    def __init__(
        self,
        working_dir: Path,
        on_stream: Callable[[str, str], None] | None = None,
        llm_config: dict[str, Any] | None = None,
        log_event: Callable[..., None] | None = None,
    ) -> None:
        """Initialize ExamineHandler.

        Args:
            working_dir: Working directory for file access
            on_stream: Optional callback for LLM streaming chunks (S3.T6)
            llm_config: Optional LLM configuration (S4.T3)
            log_event: Optional logger for hybrid events (ISSUE-OBS-002)
        """
        self._working_dir = working_dir
        self._on_stream = on_stream
        self._llm_config = llm_config or {}
        self._log_event = log_event

    def handle(self, request: ExamineRequest) -> dict[str, Any]:
        """Handle EXAMINE action.

        Args:
            request: ExamineRequest from server with base_prompt

        Returns:
            Dict with issues, thinking_budget_used, and raw_response

        Raises:
            ValueError: If request.base_prompt is None (server must provide base_prompt)
        """
        logger.info(f"Examining plan version: {request.plan_version_id}")
        print_info(f"Examining plan ({len(request.plan_items)} items)...")

        # Validate base_prompt (server-side prompting required)
        if request.base_prompt is None:
            error_msg = "ExamineRequest.base_prompt is None. Server must provide base prompt (ADR-027)."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Enrich base prompt with local tactical context
        enricher = PromptEnricher(self._working_dir)
        enriched_prompt = enricher.enrich(request.base_prompt)

        provider, model, thinking_level = self._resolve_llm_config("anthropic")
        resolved_thinking_level = thinking_level if request.thinking_required else "off"

        # Invoke LLM with thinking if required
        raw_response, thinking_used, thinking_fallback = self._invoke_llm(
            enriched_prompt,
            provider=provider,
            model=model,
            thinking_level=resolved_thinking_level,
        )

        # Parse issues from response
        issues, parse_info = self._parse_issues(raw_response)
        self._log_parse_event(
            action="examine",
            provider=provider,
            model=model,
            parse_info=parse_info,
        )

        if self._should_retry_on_parse_failure(provider, model, parse_info):
            retry_prompt = self._build_retry_prompt(enriched_prompt)
            self._log_retry_event(
                action="examine",
                provider=provider,
                model=model,
                attempt=1,
                reason=parse_info.get("status", "unknown"),
            )
            raw_response, thinking_used, thinking_fallback = self._invoke_llm(
                retry_prompt,
                provider=provider,
                model=model,
                thinking_level=resolved_thinking_level,
            )
            issues, parse_info = self._parse_issues(raw_response)
            parse_info["retried"] = True
            self._log_parse_event(
                action="examine",
                provider=provider,
                model=model,
                parse_info=parse_info,
            )

        logger.info(f"Found {len(issues)} issues")
        print_info(f"Found {len(issues)} issues")

        # Log blocking issues
        blocking = [i for i in issues if i.get("severity") in ("P0", "P1", "critical", "high")]
        if blocking:
            logger.info(f"  Blocking issues: {len(blocking)}")
            print_info(f"  Blocking issues: {len(blocking)}")

        return {
            "issues": issues,
            "thinking_budget_used": thinking_used,
            "thinking_fallback": thinking_fallback,
            "raw_response": raw_response,
            "iteration": 0,  # Server tracks iteration
        }

    def _invoke_llm(
        self,
        prompt: str,
        *,
        provider: str,
        model: str,
        thinking_level: str,
    ) -> tuple[str, int, bool]:
        """Invoke LLM for examination.

        Args:
            prompt: Examination prompt
            provider: LLM provider name
            model: LLM model name
            thinking_level: Thinking level (standard, high, max)

        Returns:
            Tuple of (raw_response, thinking_tokens_used, thinking_fallback)
        """
        logger.debug(
            f"Invoking LLM via CLI: provider={provider} model={model} "
            f"thinking_level={thinking_level}"
        )

        def _stream(chunk: str) -> None:
            if self._on_stream:
                self._on_stream("llm_streaming", chunk)

        try:
            schema_path = None
            if provider == "openai":
                schema = {
                    "type": "object",
                    "properties": {
                        "issues": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "category": {"type": "string"},
                                    "severity": {"type": "string"},
                                    "description": {"type": "string"},
                                    "affected_items": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "required": [
                                    "id",
                                    "category",
                                    "severity",
                                    "description",
                                    "affected_items",
                                ],
                            },
                        }
                    },
                    "required": ["issues"],
                }
                with tempfile.NamedTemporaryFile(
                    mode="w+",
                    delete=False,
                    encoding="utf-8",
                ) as schema_file:
                    json.dump(schema, schema_file)
                    schema_path = Path(schema_file.name)
            try:
                response = invoke_llm_via_cli(
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
            return response, 0, False
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            return json.dumps({"issues": []}), 0, False

    def _parse_issues(self, raw_response: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Parse LLM response into issues list.

        Args:
            raw_response: Raw LLM response

        Returns:
            List of issue dictionaries
        """
        parse_info = {
            "status": "strict_json",
            "response_length": len(raw_response),
            "used_extraction": False,
        }
        try:
            # Try to extract JSON from response
            response = raw_response.strip()

            if response.startswith("```"):
                lines = response.split("\n")
                start = 1 if lines[0].startswith("```") else 0
                end = len(lines) - 1 if lines[-1] == "```" else len(lines)
                response = "\n".join(lines[start:end])

            # Parse JSON
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                candidate = extract_json_payload(raw_response)
                if candidate and candidate != response:
                    parse_info["status"] = "tolerant_json"
                    parse_info["used_extraction"] = True
                    data = json.loads(candidate)

            # ISSUE-SAAS-030 FIX: Handle Claude CLI JSON wrapper format
            data, was_unwrapped = unwrap_claude_cli_json(data)
            if was_unwrapped:
                logger.debug("Detected Claude CLI JSON wrapper, extracted result field")
                parse_info["unwrapped_cli_json"] = True
                if isinstance(data, str):
                    # Unwrapped result is text, not JSON - no issues to parse
                    logger.warning("Claude CLI result is text, not JSON; assuming no issues.")
                    parse_info["status"] = "coerced_text"
                    return [], parse_info
                # Otherwise data is dict/list, continue processing below

            # Extract issues
            if isinstance(data, dict) and "issues" in data:
                issues = data["issues"]
            elif isinstance(data, list):
                issues = data
            else:
                logger.warning("Unexpected response format")
                parse_info["status"] = "empty_fallback"
                return [], parse_info

            # Validate and normalize issues
            normalized = []
            for i, issue in enumerate(issues):
                normalized_issue = {
                    "id": issue.get("id", f"I{i + 1}"),
                    "category": issue.get("category", "other"),
                    "severity": self._normalize_severity(issue.get("severity", "low")),
                    "description": issue.get("description", ""),
                    "affected_items": issue.get("affected_items", []),
                }
                normalized.append(normalized_issue)

            return normalized, parse_info

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse issues JSON: {e}")
            parse_info["status"] = "parse_error_fallback"
            parse_info["error"] = str(e)
            return [], parse_info

    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity string.

        Args:
            severity: Raw severity string

        Returns:
            Normalized severity (critical, high, medium, low, or P0-P3)
        """
        severity_lower = severity.lower()

        # Map common severity strings
        mapping = {
            "critical": "critical",
            "p0": "P0",
            "blocker": "critical",
            "high": "high",
            "p1": "P1",
            "major": "high",
            "medium": "medium",
            "p2": "P2",
            "minor": "medium",
            "low": "low",
            "p3": "P3",
            "trivial": "low",
        }

        return mapping.get(severity_lower, severity)

    def _resolve_llm_config(self, default_provider: str) -> tuple[str, str, str]:
        resolved_provider = self._llm_config.get("provider", default_provider)
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
        if parse_info.get("status") not in ("empty_fallback", "parse_error_fallback"):
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


__all__ = ["ExamineHandler"]
