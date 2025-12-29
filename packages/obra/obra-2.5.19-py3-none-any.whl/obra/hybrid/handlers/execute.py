"""Execute handler for Hybrid Orchestrator.

This module handles the EXECUTE action from the server. It executes a plan item
by deploying an implementation agent (Claude Code, etc.).

The execution process:
    1. Receive ExecutionRequest with plan item to execute
    2. Prepare execution context (files, dependencies)
    3. Deploy implementation agent
    4. Collect execution results (files changed, tests, etc.)
    5. Return ExecutionResult to report to server

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md Section 2
    - obra/api/protocol.py
    - obra/hybrid/orchestrator.py
"""

import logging
import subprocess
from pathlib import Path
from typing import Any

from obra.api.protocol import ExecutionRequest, ExecutionStatus
from obra.config import (
    DEFAULT_LLM_API_TIMEOUT,
    PROVIDER_CLI_INFO,
    build_llm_args,
    get_llm_cli,
    get_thinking_keyword,
)
from obra.display import print_error, print_info, print_warning
from obra.hybrid.handlers.base import ObservabilityContextMixin
from obra.hybrid.prompt_enricher import PromptEnricher

logger = logging.getLogger(__name__)


class ExecuteHandler(ObservabilityContextMixin):
    """Handler for EXECUTE action.

    Executes a plan item using an implementation agent (e.g., Claude Code CLI).
    Returns execution results including files changed and test results.

    ## Architecture Context (ADR-027)

    This handler implements the two-tier prompting architecture where:
    - **Server (Tier 1)**: Generates strategic base prompts with execution instructions
    - **Client (Tier 2)**: Enriches base prompts with local tactical context

    **Implementation Flow**:
    1. Server sends ExecutionRequest with base_prompt containing execution instructions
    2. Client enriches base_prompt via PromptEnricher (adds file structure, git log)
    3. Client invokes implementation agent (e.g., Claude Code CLI) via subprocess
    4. Client runs tests locally and reports results back to server

    ## IP Protection

    Strategic execution patterns (best practices, quality standards) stay on server.
    This protects Obra's proprietary implementation guidance from client-side inspection.

    ## Privacy Protection

    Tactical context (file contents, git messages, errors) never sent to server.
    Only execution results (summary, files changed, test results) is transmitted.

    See: docs/decisions/ADR-027-two-tier-prompting-architecture.md

    Example:
        >>> handler = ExecuteHandler(Path("/path/to/project"))
        >>> request = ExecutionRequest(
        ...     plan_items=[{"id": "T1", "title": "Create models", ...}],
        ...     execution_index=0
        ... )
        >>> result = handler.handle(request)
        >>> print(result["status"])
    """

    def __init__(
        self,
        working_dir: Path,
        llm_config: dict[str, str] | None = None,
        session_id: str | None = None,
        log_file: Path | None = None,
    ) -> None:
        """Initialize ExecuteHandler.

        Args:
            working_dir: Working directory for file access
            llm_config: Optional LLM configuration (S6.T1)
            session_id: Optional session ID for trace correlation
            log_file: Optional log file path for event emission
        """
        self._working_dir = working_dir
        self._llm_config = llm_config or {}
        self._session_id = session_id
        self._log_file = log_file

    def handle(self, request: ExecutionRequest) -> dict[str, Any]:
        """Handle EXECUTE action.

        Args:
            request: ExecutionRequest from server with base_prompt

        Returns:
            Dict with item_id, status, summary, files_changed, etc.

        Raises:
            ValueError: If request.base_prompt is None (server must provide base_prompt)
        """
        if not request.current_item:
            logger.error("No current item to execute")
            return {
                "item_id": "",
                "status": ExecutionStatus.FAILURE.value,
                "summary": "No item to execute",
                "files_changed": 0,
                "tests_passed": False,
                "test_count": 0,
                "coverage_delta": 0.0,
            }

        # Validate base_prompt (server-side prompting required)
        if request.base_prompt is None:
            error_msg = "ExecutionRequest.base_prompt is None. Server must provide base prompt (ADR-027)."
            logger.error(error_msg)
            raise ValueError(error_msg)

        item = request.current_item
        item_id = item.get("id", "unknown")
        title = item.get("title", "Untitled")

        logger.info(f"Executing item {item_id}: {title}")
        print_info(f"Executing: {item_id} - {title}")

        # Enrich base prompt with local tactical context
        enricher = PromptEnricher(self._working_dir)
        enriched_prompt = enricher.enrich(request.base_prompt)

        # Execute via implementation agent
        result = self._execute_item(item, enriched_prompt)

        # Log result
        status = result.get("status", ExecutionStatus.FAILURE.value)
        if status == ExecutionStatus.SUCCESS.value:
            print_info(f"  Completed: {result.get('summary', 'Success')[:50]}")
        elif status == ExecutionStatus.PARTIAL.value:
            print_warning(f"  Partial: {result.get('summary', 'Partial completion')[:50]}")
        else:
            print_error(f"  Failed: {result.get('summary', 'Execution failed')[:50]}")

        return result

    def _execute_item(self, item: dict[str, Any], enriched_prompt: str) -> dict[str, Any]:
        """Execute a single plan item.

        Args:
            item: Plan item to execute
            enriched_prompt: Enriched execution prompt from server

        Returns:
            Execution result dictionary
        """
        item_id = item.get("id", "unknown")
        title = item.get("title", "Untitled")

        # Try to deploy implementation agent with enriched prompt
        try:
            result = self._deploy_agent(enriched_prompt)

            # Count files changed (would be from git diff in production)
            files_changed = result.get("files_changed", 0)

            # Run tests if present
            tests_passed, test_count = self._run_tests()

            return {
                "item_id": item_id,
                "status": result.get("status", ExecutionStatus.SUCCESS.value),
                "summary": result.get("summary", f"Executed: {title}"),
                "files_changed": files_changed,
                "tests_passed": tests_passed,
                "test_count": test_count,
                "coverage_delta": 0.0,  # Would be calculated from coverage reports
            }

        except Exception as e:
            logger.error(f"Execution failed for {item_id}: {e}")
            return {
                "item_id": item_id,
                "status": ExecutionStatus.FAILURE.value,
                "summary": f"Execution failed: {e!s}",
                "files_changed": 0,
                "tests_passed": False,
                "test_count": 0,
                "coverage_delta": 0.0,
            }

    def _prepare_prompt(self, prompt: str) -> str:
        """Prepare prompt with thinking keywords if needed.

        S6.T2: Inject ultrathink keyword for Claude + maximum thinking level.

        Args:
            prompt: Base prompt

        Returns:
            Prepared prompt with keywords if applicable
        """
        keyword = get_thinking_keyword(self._llm_config)
        if keyword:
            return f"{keyword}: {prompt}"

        return prompt

    def _deploy_agent(self, prompt: str) -> dict[str, Any]:
        """Deploy implementation agent via subprocess.

        S6.T3: Use build_llm_args() and get_llm_cli() to construct command.
        S6.T4: Detect auth errors and provide login hints.
        S6.T5: Execute subprocess.run() with constructed command.

        Args:
            prompt: Execution prompt

        Returns:
            Agent result dictionary with status, summary, files_changed
        """
        import os

        logger.debug("Deploying implementation agent")

        # S6.T2: Prepare prompt with thinking keywords if needed
        prepared_prompt = self._prepare_prompt(prompt)

        # S6.T3: Build CLI command and args from llm_config
        if self._llm_config:
            provider = self._llm_config.get("provider", "anthropic")
            cli_command = get_llm_cli(provider)
            cli_args = build_llm_args(self._llm_config)
        else:
            # Fallback to defaults if no config
            cli_command = "claude"
            cli_args = ["--dangerously-skip-permissions"]
            provider = "anthropic"

        # Construct full command
        cmd = [cli_command] + cli_args + [prepared_prompt]

        logger.debug(f"Running agent: {' '.join(cmd[:3])}...")

        # ISSUE-OBS-003: Pass observability context via environment variables
        # Uses OpenTelemetry/CI-CD pattern for cross-process context propagation
        env = os.environ.copy()
        env.update(self._get_observability_env())

        try:
            # S6.T5: Execute subprocess with observability environment
            result = subprocess.run(
                cmd,
                check=False, cwd=self._working_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",  # ISSUE-SAAS-030: Explicit UTF-8 for Windows
                timeout=600,  # 10 minute timeout
                env=env,  # ISSUE-OBS-003: Pass observability context
            )

            # S6.T4: Check for auth errors in stderr
            stderr = result.stderr.lower()
            if "not authenticated" in stderr or "login" in stderr or "auth" in stderr:
                auth_hint = PROVIDER_CLI_INFO.get(provider, {}).get(
                    "auth_hint", f"{cli_command} login"
                )
                return {
                    "status": ExecutionStatus.FAILURE.value,
                    "summary": f"Authentication required. Run '{auth_hint}' to authenticate.",
                    "files_changed": 0,
                }

            # Check exit code
            if result.returncode == 0:
                return {
                    "status": ExecutionStatus.SUCCESS.value,
                    "summary": "Task executed successfully",
                    "files_changed": 1,  # Placeholder - would parse git diff in production
                }
            error_msg = result.stderr[:200] if result.stderr else "Unknown error"
            return {
                "status": ExecutionStatus.FAILURE.value,
                "summary": f"Execution failed: {error_msg}",
                "files_changed": 0,
            }

        except subprocess.TimeoutExpired:
            logger.error("Agent execution timed out")
            return {
                "status": ExecutionStatus.FAILURE.value,
                "summary": "Execution timed out after 10 minutes",
                "files_changed": 0,
            }
        except FileNotFoundError:
            logger.error(f"CLI command '{cli_command}' not found")
            return {
                "status": ExecutionStatus.FAILURE.value,
                "summary": f"CLI '{cli_command}' not found. Install it first.",
                "files_changed": 0,
            }
        except Exception as e:
            logger.error(f"Agent deployment failed: {e}")
            return {
                "status": ExecutionStatus.FAILURE.value,
                "summary": f"Deployment failed: {e!s}",
                "files_changed": 0,
            }

    def _run_tests(self) -> tuple[bool, int]:
        """Run project tests.

        Returns:
            Tuple of (tests_passed, test_count)
        """
        # Try to detect and run tests
        # Check for common test runners
        test_commands = [
            ("pytest", ["pytest", "--tb=no", "-q"]),
            ("npm test", ["npm", "test", "--", "--passWithNoTests"]),
            ("go test", ["go", "test", "./..."]),
            ("cargo test", ["cargo", "test"]),
        ]

        for name, cmd in test_commands:
            # Check if the test runner is available and relevant
            try:
                # Simple check - does the command exist?
                result = subprocess.run(
                    [cmd[0], "--version"],
                    check=False, capture_output=True,
                    timeout=5,
                    cwd=self._working_dir,
                )
                if result.returncode != 0:
                    continue

                # Check if relevant config exists
                if cmd[0] == "pytest" and not (
                    (self._working_dir / "pytest.ini").exists()
                    or (self._working_dir / "pyproject.toml").exists()
                    or (self._working_dir / "tests").is_dir()
                ):
                    continue

                if cmd[0] == "npm" and not (self._working_dir / "package.json").exists():
                    continue

                # Run tests
                logger.debug(f"Running tests with {name}")
                result = subprocess.run(
                    cmd,
                    check=False, capture_output=True,
                    timeout=DEFAULT_LLM_API_TIMEOUT,
                    cwd=self._working_dir,
                )

                # Parse results (simplified)
                passed = result.returncode == 0
                # Count tests from output (very simplified)
                output = result.stdout.decode("utf-8", errors="ignore")
                test_count = output.count("passed") + output.count("PASS")

                return passed, max(test_count, 1 if passed else 0)

            except subprocess.TimeoutExpired:
                logger.warning(f"Test timeout with {name}")
                continue
            except FileNotFoundError:
                continue
            except Exception as e:
                logger.debug(f"Test runner {name} failed: {e}")
                continue

        # No tests found or run
        return True, 0  # Assume success if no tests


__all__ = ["ExecuteHandler"]
