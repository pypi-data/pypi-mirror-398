"""Revise handler for Hybrid Orchestrator.

This module handles the REVISE action from the server. It revises the current
plan based on issues identified during examination.

The revision process:
    1. Receive RevisionRequest with issues to address
    2. Build revision prompt with issues and guidance
    3. Invoke LLM to generate revised plan
    4. Parse revised plan items
    5. Return RevisedPlan to report to server

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md Section 1
    - obra/api/protocol.py
    - obra/hybrid/orchestrator.py
"""

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from obra.api.protocol import RevisionRequest
from obra.display import print_info
from obra.hybrid.json_utils import extract_json_payload, unwrap_claude_cli_json
from obra.hybrid.prompt_enricher import PromptEnricher
from obra.llm.cli_runner import invoke_llm_via_cli
from obra.model_registry import get_default_model, validate_model

logger = logging.getLogger(__name__)


class ReviseHandler:
    """Handler for REVISE action.

    Revises the current plan based on issues from examination.
    Returns updated plan items with changes summary.

    ## Architecture Context (ADR-027)

    This handler implements the two-tier prompting architecture where:
    - **Server (Tier 1)**: Generates strategic base prompts with revision guidance
    - **Client (Tier 2)**: Enriches base prompts with local tactical context

    **Implementation Flow**:
    1. Server sends RevisionRequest with base_prompt containing revision instructions
    2. Client enriches base_prompt via PromptEnricher (adds file structure, git log)
    3. Client invokes LLM with enriched prompt locally
    4. Client reports revised plan items and changes summary back to server

    ## IP Protection

    Strategic revision guidance (issue patterns, quality standards) stay on server.
    This protects Obra's proprietary quality assessment IP from client-side inspection.

    ## Privacy Protection

    Tactical context (file contents, git messages, errors) never sent to server.
    Only LLM revision results (revised plan and changes summary) is transmitted.

    See: docs/decisions/ADR-027-two-tier-prompting-architecture.md

    Example:
        >>> handler = ReviseHandler(Path("/path/to/project"))
        >>> request = RevisionRequest(
        ...     issues=[{"id": "I1", "description": "Missing error handling"}],
        ...     blocking_issues=[{"id": "I1", ...}]
        ... )
        >>> result = handler.handle(request)
        >>> print(result["plan_items"])
    """

    def __init__(
        self,
        working_dir: Path,
        on_stream: Callable[[str, str], None] | None = None,
        llm_config: dict[str, str] | None = None,
        log_event: Callable[..., None] | None = None,
    ) -> None:
        """Initialize ReviseHandler.

        Args:
            working_dir: Working directory for file access
            on_stream: Optional callback for LLM streaming chunks (S3.T6)
            llm_config: Optional LLM configuration (S4.T4)
            log_event: Optional logger for hybrid events (ISSUE-OBS-002)
        """
        self._working_dir = working_dir
        self._on_stream = on_stream
        self._llm_config = llm_config or {}
        self._log_event = log_event

    def handle(self, request: RevisionRequest) -> dict[str, Any]:
        """Handle REVISE action.

        Args:
            request: RevisionRequest from server with base_prompt

        Returns:
            Dict with plan_items, changes_summary, and raw_response

        Raises:
            ValueError: If request.base_prompt is None (server must provide base_prompt)
        """
        logger.info(f"Revising plan to address {len(request.issues)} issues")
        print_info(f"Revising plan ({len(request.blocking_issues)} blocking issues)...")

        # Validate base_prompt (server-side prompting required)
        if request.base_prompt is None:
            error_msg = "RevisionRequest.base_prompt is None. Server must provide base prompt (ADR-027)."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Enrich base prompt with local tactical context
        enricher = PromptEnricher(self._working_dir)
        enriched_prompt = enricher.enrich(request.base_prompt)

        provider, model, thinking_level = self._resolve_llm_config("anthropic")

        # Invoke LLM with enriched prompt
        raw_response = self._invoke_llm(
            enriched_prompt,
            provider=provider,
            model=model,
            thinking_level=thinking_level,
        )

        # Parse revised plan
        plan_items, changes_summary, parse_info = self._parse_revision(raw_response)
        self._log_parse_event(
            action="revise",
            provider=provider,
            model=model,
            parse_info=parse_info,
        )

        if self._should_retry_on_parse_failure(provider, model, parse_info):
            retry_prompt = self._build_retry_prompt(enriched_prompt)
            self._log_retry_event(
                action="revise",
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
            plan_items, changes_summary, parse_info = self._parse_revision(raw_response)
            parse_info["retried"] = True
            self._log_parse_event(
                action="revise",
                provider=provider,
                model=model,
                parse_info=parse_info,
            )

        logger.info(f"Revised plan has {len(plan_items)} items")
        print_info(f"Revised plan: {len(plan_items)} items")

        return {
            "plan_items": plan_items,
            "changes_summary": changes_summary,
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
        """Invoke LLM for revision.

        Args:
            prompt: Revision prompt
            provider: LLM provider name
            model: LLM model name
            thinking_level: LLM thinking level

        Returns:
            Raw LLM response
        """
        logger.debug(f"Invoking LLM via CLI for revision: provider={provider} model={model}")

        def _stream(chunk: str) -> None:
            if self._on_stream:
                self._on_stream("llm_streaming", chunk)

        try:
            return invoke_llm_via_cli(
                prompt=prompt,
                cwd=self._working_dir,
                provider=provider,
                model=model,
                thinking_level=thinking_level,
                on_stream=_stream if self._on_stream else None,
            )
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            return json.dumps(
                {
                    "plan_items": [],
                    "changes_summary": f"LLM error: {e!s}",
                }
            )

    def _parse_revision(
        self,
        raw_response: str,
    ) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
        """Parse LLM response into revised plan.

        Args:
            raw_response: Raw LLM response

        Returns:
            Tuple of (plan_items, changes_summary, parse_info)
        """
        parse_info = {
            "status": "strict_json",
            "used_extraction": False,
            "response_length": len(raw_response or ""),
        }

        response = raw_response.strip()
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            candidate = extract_json_payload(raw_response)
            if candidate and candidate != response:
                parse_info["status"] = "tolerant_json"
                parse_info["used_extraction"] = True
                data = json.loads(candidate)
            else:
                parse_info["status"] = "parse_error_fallback"
                return (
                    self._build_parse_error_fallback(raw_response),
                    f"Parse error: {e!s}",
                    parse_info,
                )

        # ISSUE-SAAS-030 FIX: Handle Claude CLI JSON wrapper format
        data, was_unwrapped = unwrap_claude_cli_json(data)
        if was_unwrapped:
            logger.debug("Detected Claude CLI JSON wrapper, extracted result field")
            parse_info["unwrapped_cli_json"] = True
            if isinstance(data, str):
                logger.warning("Claude CLI result is text, not JSON; returning empty revision.")
                parse_info["status"] = "coerced_text"
                return [], "", parse_info
            # Otherwise data is dict/list, continue processing below

        if isinstance(data, dict):
            items = data.get("plan_items", [])
            summary = data.get("changes_summary", "")
        elif isinstance(data, list):
            items = data
            summary = ""
        else:
            logger.warning("Unexpected response format")
            parse_info["status"] = "unexpected_format"
            return (
                self._build_parse_error_fallback(raw_response),
                "Parse error: Unexpected response format",
                parse_info,
            )

        if not items:
            parse_info["status"] = "empty_items"
            return (
                self._build_parse_error_fallback(raw_response),
                "Parse error: Empty plan_items",
                parse_info,
            )

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

        return normalized, summary, parse_info

    def _build_parse_error_fallback(self, raw_response: str) -> list[dict[str, Any]]:
        preview = (raw_response or "").strip().replace("\n", " ")[:240]
        description = (
            "Revision response was not valid JSON. "
            "Manual review required.\n\n"
            f"Response preview: {preview}"
        )
        return [
            {
                "id": "REVISION_PARSE_ERROR",
                "item_type": "task",
                "title": "Revision parse error - manual review required",
                "description": description,
                "acceptance_criteria": [
                    "Review revision output for JSON formatting errors",
                    "Retry revision with corrected JSON-only output",
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
        if parse_info.get("status") not in ("parse_error_fallback", "empty_items"):
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
            logger.warning(f"Failed to log parse event for {action}: {e}")

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
            logger.warning(f"Failed to log parse retry event for {action}: {e}")


__all__ = ["ReviseHandler"]
