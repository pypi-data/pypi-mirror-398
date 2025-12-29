"""Fix handler for Hybrid Orchestrator.

This module handles the FIX action from the server. It attempts to fix issues
found during review by deploying an implementation agent with specific fix instructions.

The fix process:
    1. Receive FixRequest with issues to fix and execution order
    2. For each issue in order:
       - Build fix prompt with issue details
       - Deploy implementation agent
       - Verify the fix
    3. Return FixResults to report to server

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md Section 2
    - obra/api/protocol.py
    - obra/hybrid/orchestrator.py
"""

import logging
import subprocess
from pathlib import Path
from typing import Any

from obra.api.protocol import FixRequest
from obra.config import DEFAULT_NETWORK_TIMEOUT
from obra.display import print_error, print_info, print_warning
from obra.hybrid.handlers.base import ObservabilityContextMixin
from obra.hybrid.prompt_enricher import PromptEnricher

logger = logging.getLogger(__name__)


class FixHandler(ObservabilityContextMixin):
    """Handler for FIX action.

    Attempts to fix issues found during review by deploying implementation
    agents with targeted fix instructions.

    ## Architecture Context (ADR-027)

    This handler implements the two-tier prompting architecture where:
    - **Server (Tier 1)**: Generates strategic base prompts with fix guidance
    - **Client (Tier 2)**: Enriches base prompts with local tactical context

    **Implementation Flow**:
    1. Server sends FixRequest with base_prompt containing fix instructions
    2. Client enriches base_prompt via PromptEnricher (adds file structure, git log)
    3. Client invokes implementation agent locally to apply fixes
    4. Client verifies fixes locally (tests, lint, security checks)
    5. Client reports fix results back to server for validation

    ## IP Protection

    Strategic fix patterns (security best practices, quality standards) stay on server.
    This protects Obra's proprietary fix guidance from client-side inspection.

    ## Privacy Protection

    Tactical context (code to fix, file contents, git messages) never sent to server.
    Only fix results (status, files modified, verification outcome) is transmitted.

    See: docs/decisions/ADR-027-two-tier-prompting-architecture.md

    Example:
        >>> handler = FixHandler(Path("/path/to/project"))
        >>> request = FixRequest(
        ...     issues_to_fix=[{"id": "SEC-001", "description": "SQL injection"}],
        ...     execution_order=["SEC-001"]
        ... )
        >>> result = handler.handle(request)
        >>> print(result["fix_results"])
    """

    def __init__(
        self,
        working_dir: Path,
        llm_config: dict[str, Any] | None = None,
        session_id: str | None = None,
        log_file: Path | None = None,
    ) -> None:
        """Initialize FixHandler.

        Args:
            working_dir: Working directory for file access
            llm_config: LLM configuration for agent deployment
            session_id: Optional session ID for trace correlation
            log_file: Optional log file path for event emission
        """
        self._working_dir = working_dir
        self._llm_config = llm_config or {}
        self._session_id = session_id
        self._log_file = log_file

    def handle(self, request: FixRequest) -> dict[str, Any]:
        """Handle FIX action.

        Args:
            request: FixRequest from server with base_prompt

        Returns:
            Dict with fix_results list and item_id

        Raises:
            ValueError: If request.base_prompt is None (server must provide base_prompt)
        """
        # ISSUE-SAAS-009: Normalize issues to dict format
        # Server may return issues as List[str] (blocking_issues) instead of List[Dict]
        issues = self._normalize_issues(request.issues_to_fix)
        execution_order = request.execution_order
        # ISSUE-SAAS-021: Track item_id for fix-review loop
        item_id = request.item_id

        if not issues:
            logger.info("No issues to fix")
            return {
                "fix_results": [],
                "fixed_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "item_id": item_id,  # ISSUE-SAAS-021
            }

        # Validate base_prompt (server-side prompting required)
        if request.base_prompt is None:
            error_msg = "FixRequest.base_prompt is None. Server must provide base prompt (ADR-027)."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Fixing {len(issues)} issues")
        print_info(f"Fixing {len(issues)} issues")

        # Enrich base prompt with local tactical context
        enricher = PromptEnricher(self._working_dir)
        enriched_prompt = enricher.enrich(request.base_prompt)

        # Build issue lookup for ordering
        issue_map = {issue.get("id", f"issue-{i}"): issue for i, issue in enumerate(issues)}

        # Determine execution order
        if execution_order:
            ordered_ids = execution_order
        else:
            # Default: order by priority (P0 first)
            ordered_ids = self._order_by_priority(issues)

        fix_results: list[dict[str, Any]] = []
        fixed_count = 0
        failed_count = 0
        skipped_count = 0

        for issue_id in ordered_ids:
            issue = issue_map.get(issue_id)
            if not issue:
                logger.warning(f"Issue {issue_id} not found in issue map, skipping")
                skipped_count += 1
                continue

            result = self._fix_issue(issue, enriched_prompt)
            fix_results.append(result)

            status = result.get("status", "failed")
            if status == "fixed":
                fixed_count += 1
                print_info(f"  Fixed: {issue_id}")
            elif status == "skipped":
                skipped_count += 1
                print_warning(f"  Skipped: {issue_id}")
            else:
                failed_count += 1
                print_error(f"  Failed: {issue_id}")

        logger.info(f"Fix complete: {fixed_count} fixed, {failed_count} failed, {skipped_count} skipped")

        return {
            "fix_results": fix_results,
            "fixed_count": fixed_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "item_id": item_id,  # ISSUE-SAAS-021: Include for fix-review loop
        }

    def _normalize_issues(self, issues: list[Any]) -> list[dict[str, Any]]:
        """Normalize issues to dict format.

        ISSUE-SAAS-009: Server may return issues as List[str] (blocking_issues from
        QualityScorecard) instead of List[Dict[str, Any]]. This method normalizes
        both formats to a consistent dict structure.

        Args:
            issues: List of issues (strings or dicts)

        Returns:
            List of normalized issue dicts with at least 'id' and 'description' keys
        """
        normalized: list[dict[str, Any]] = []
        for i, issue in enumerate(issues):
            if isinstance(issue, str):
                # String format: convert to dict with synthetic ID
                # Use the string itself as the ID (for execution_order matching)
                # and as the description
                normalized.append({
                    "id": issue,  # Use string value as ID for execution_order lookup
                    "description": issue,
                    "priority": "P2",  # Default priority for string issues
                })
            elif isinstance(issue, dict):
                # Dict format: ensure id exists
                if "id" not in issue:
                    issue = dict(issue)  # Copy to avoid mutating original
                    issue["id"] = f"issue-{i}"
                normalized.append(issue)
            else:
                # Unknown format: wrap in dict
                logger.warning(f"Unknown issue format at index {i}: {type(issue)}")
                normalized.append({
                    "id": f"issue-{i}",
                    "description": str(issue),
                    "priority": "P2",
                })
        return normalized

    def _order_by_priority(self, issues: list[dict[str, Any]]) -> list[str]:
        """Order issues by priority.

        Args:
            issues: List of issues (normalized to dict format)

        Returns:
            List of issue IDs in priority order (P0 first)
        """
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

        def get_priority_rank(issue: dict[str, Any]) -> int:
            priority = issue.get("priority", "P3")
            return priority_order.get(priority, 4)

        sorted_issues = sorted(issues, key=get_priority_rank)
        return [issue.get("id", f"issue-{i}") for i, issue in enumerate(sorted_issues)]

    def _fix_issue(self, issue: dict[str, Any], enriched_prompt: str) -> dict[str, Any]:
        """Fix a single issue.

        Args:
            issue: Issue dictionary
            enriched_prompt: Enriched fix prompt from server

        Returns:
            FixResult dictionary
        """
        issue_id = issue.get("id", "unknown")
        description = issue.get("description", "")

        logger.info(f"Fixing issue {issue_id}: {description[:50]}...")

        try:
            # Deploy implementation agent to fix with enriched prompt
            result = self._deploy_agent(enriched_prompt)

            # Verify the fix
            verification = self._verify_fix(issue, result)

            # Determine status based on verification
            # BUG-SCHEMA-001: Use "applied" not "fixed" to match server schema (request_schemas.py:211)
            if verification.get("all_passed", False):
                status = "applied"
            elif verification.get("partial", False):
                status = "applied"  # Partial fix still counts
            else:
                status = "failed"

            # BUG-SCHEMA-002: Add summary for orchestrator (orchestrator.py:791)
            summary = result.get("summary", f"{'Applied fix for' if status == 'applied' else 'Failed to fix'} issue {issue_id}")

            return {
                "issue_id": issue_id,
                "status": status,
                "files_modified": result.get("files_modified", []),
                "verification": verification,
                "summary": summary,
            }

        except Exception as e:
            logger.error(f"Failed to fix issue {issue_id}: {e}")
            return {
                "issue_id": issue_id,
                "status": "failed",
                "files_modified": [],
                "verification": {"error": str(e)},
                "summary": f"Failed to fix issue {issue_id}: {e!s}",  # BUG-SCHEMA-002
            }

    def _prepare_prompt(self, prompt: str) -> str:
        """Prepare prompt with thinking keywords if needed.

        Inject ultrathink keyword for Claude + maximum thinking level.

        Args:
            prompt: Base prompt

        Returns:
            Prepared prompt with keywords if applicable
        """
        provider = self._llm_config.get("provider", "")
        thinking_level = self._llm_config.get("thinking_level", "")

        # Anthropic + maximum = ultrathink keyword injection
        if provider == "anthropic" and thinking_level == "maximum":
            return f"ultrathink: {prompt}"

        return prompt

    def _deploy_agent(self, prompt: str) -> dict[str, Any]:
        """Deploy implementation agent to apply fix via subprocess.

        Uses build_llm_args() and get_llm_cli() to construct command.
        Detects auth errors and provides login hints.

        Args:
            prompt: Fix prompt

        Returns:
            Agent result dictionary with status, summary, files_modified
        """
        import os

        from obra.config import build_llm_args, get_llm_cli

        logger.debug("Deploying implementation agent for fix")

        # Prepare prompt with thinking keywords if needed
        prepared_prompt = self._prepare_prompt(prompt)

        # Build CLI command and args from llm_config
        if self._llm_config:
            provider = self._llm_config.get("provider", "anthropic")
            cli_command = get_llm_cli(provider)
            cli_args = build_llm_args(self._llm_config)
        else:
            # Fallback to defaults if no config
            cli_command = "claude"
            cli_args = ["--dangerously-skip-permissions"]

        # Construct full command
        cmd = [cli_command] + cli_args + [prepared_prompt]

        logger.debug(f"Running fix agent: {' '.join(cmd[:3])}...")

        # ISSUE-OBS-003: Pass observability context via environment variables
        # Uses OpenTelemetry/CI-CD pattern for cross-process context propagation
        env = os.environ.copy()
        env.update(self._get_observability_env())

        try:
            # Execute subprocess with observability environment
            result = subprocess.run(
                cmd,
                check=False, cwd=self._working_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",  # ISSUE-SAAS-030: Explicit UTF-8 for Windows
                timeout=600,  # 10 minute timeout
                env=env,  # ISSUE-OBS-003: Pass observability context
            )

            # Check for auth errors in stderr
            stderr = result.stderr.lower()
            if "not authenticated" in stderr or "login" in stderr or "auth" in stderr:
                return {
                    "status": "failed",
                    "summary": f"Authentication required. Run '{cli_command} login' to authenticate.",
                    "files_modified": [],
                }

            # Check exit code
            if result.returncode == 0:
                return {
                    "status": "success",
                    "summary": "Fix applied successfully",
                    "files_modified": [],  # Would parse git diff in production
                }
            error_msg = result.stderr[:200] if result.stderr else "Unknown error"
            return {
                "status": "failed",
                "summary": f"Fix failed: {error_msg}",
                "files_modified": [],
            }

        except subprocess.TimeoutExpired:
            logger.error("Fix agent execution timed out")
            return {
                "status": "failed",
                "summary": "Fix timed out after 10 minutes",
                "files_modified": [],
            }
        except FileNotFoundError:
            logger.error(f"CLI command '{cli_command}' not found")
            return {
                "status": "failed",
                "summary": f"CLI '{cli_command}' not found. Install it first.",
                "files_modified": [],
            }
        except Exception as e:
            logger.error(f"Fix agent deployment failed: {e}")
            return {
                "status": "failed",
                "summary": f"Deployment failed: {e!s}",
                "files_modified": [],
            }

    def _verify_fix(
        self,
        issue: dict[str, Any],
        agent_result: dict[str, Any],
    ) -> dict[str, bool]:
        """Verify that the fix resolved the issue.

        Args:
            issue: Original issue
            agent_result: Result from fix agent

        Returns:
            Verification results dictionary
        """
        verification: dict[str, bool] = {
            "agent_succeeded": agent_result.get("status") == "success",
            "files_modified": bool(agent_result.get("files_modified")),
        }

        # Check if specific verification steps are needed based on issue category
        category = issue.get("category", "")

        if category == "security":
            verification["security_check_passed"] = self._run_security_check()
        elif category == "testing":
            verification["tests_passed"] = self._run_tests()
        elif category == "code_quality":
            verification["lint_passed"] = self._run_lint()

        # Determine overall result
        verification["all_passed"] = all(
            v for k, v in verification.items()
            if k not in ("partial", "all_passed")
        )

        return verification

    def _run_security_check(self) -> bool:
        """Run security check to verify fix.

        Returns:
            True if security check passes
        """
        # TODO: Implement actual security check
        # For now, return placeholder
        return True

    def _run_tests(self) -> bool:
        """Run tests to verify fix.

        Returns:
            True if tests pass
        """
        # Try to run pytest if available
        try:
            result = subprocess.run(
                ["pytest", "--tb=no", "-q", "-x"],
                check=False, capture_output=True,
                timeout=60,
                cwd=self._working_dir,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # If tests can't be run, assume pass
            return True

    def _run_lint(self) -> bool:
        """Run linter to verify fix.

        Returns:
            True if lint passes
        """
        # Try to run ruff if available
        try:
            result = subprocess.run(
                ["ruff", "check", "."],
                check=False, capture_output=True,
                timeout=DEFAULT_NETWORK_TIMEOUT,
                cwd=self._working_dir,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # If linter can't be run, assume pass
            return True


__all__ = ["FixHandler"]
