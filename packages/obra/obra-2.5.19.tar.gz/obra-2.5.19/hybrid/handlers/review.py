"""Review handler for Hybrid Orchestrator.

This module handles the REVIEW action from the server. It deploys review agents
to analyze executed code for quality, security, testing, and documentation.

The review process:
    1. Receive ReviewRequest with item_id and agents to run
    2. Deploy each specified review agent via AgentDeployer
    3. Collect agent reports (issues, scores, execution time)
    4. Return AgentReports to report to server

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md Section 2
    - obra/api/protocol.py
    - obra/hybrid/orchestrator.py
    - obra/agents/ (S9 implementation)
"""

import logging
import subprocess
from pathlib import Path
from typing import Any

from obra.agents import AgentDeployer
from obra.api.protocol import AgentType, ReviewRequest
from obra.display import print_error, print_info, print_warning
from obra.security import PromptSanitizer

logger = logging.getLogger(__name__)


class ReviewHandler:
    """Handler for REVIEW action.

    Deploys review agents to analyze executed code and collects their reports.
    Each agent analyzes different dimensions: security, testing, docs, code quality.

    ## Architecture Context (ADR-027)

    This handler is part of the hybrid client-server architecture where:
    - **Server**: Provides orchestration decisions and specifies which agents to run
    - **Client**: Deploys agents locally and collects reports

    **Current Implementation**:
    1. Server sends ReviewRequest with item_id and agents to run
    2. Client deploys each specified review agent locally via AgentDeployer
    3. Agents analyze the codebase locally (no LLM prompts involved)
    4. Client collects agent reports (issues, scores)
    5. Client reports aggregated results back to server for validation

    Note: This handler uses the agent framework, not LLM prompt building.
    No marker-based enrichment applies to review agents.

    ## Privacy Protection

    Tactical context (code to review, file contents, git messages) never sent to server.
    Only aggregated review reports (issues summary, scores) is transmitted.

    See: docs/decisions/ADR-027-two-tier-prompting-architecture.md

    Example:
        >>> handler = ReviewHandler(Path("/path/to/project"))
        >>> request = ReviewRequest(
        ...     item_id="T1",
        ...     agents_to_run=["security", "testing"]
        ... )
        >>> result = handler.handle(request)
        >>> print(result["agent_reports"])
    """

    def __init__(self, working_dir: Path) -> None:
        """Initialize ReviewHandler.

        Args:
            working_dir: Working directory for file access
        """
        self._working_dir = working_dir
        self._deployer = AgentDeployer(working_dir)
        self._sanitizer = PromptSanitizer()

    def handle(self, request: ReviewRequest) -> dict[str, Any]:
        """Handle REVIEW action.

        Args:
            request: ReviewRequest from server

        Returns:
            Dict with agent_reports list
        """
        logger.info(f"Starting review for item: {request.item_id}")
        print_info(f"Running review agents for: {request.item_id}")

        agent_reports: list[dict[str, Any]] = []
        agents_to_run = request.agents_to_run
        changed_files = self._get_changed_files()

        # Default to all agents if none specified
        if not agents_to_run:
            agents_to_run = [at.value for at in AgentType]

        for agent_name in agents_to_run:
            try:
                agent_type = AgentType(agent_name)
            except ValueError:
                logger.warning(f"Unknown agent type: {agent_name}, skipping")
                continue

            # Get budget for this agent
            budget = request.agent_budgets.get(agent_name, {})
            timeout_ms = budget.get("timeout_ms", 60000)  # Default 60s

            # Deploy agent and collect report
            report = self._deploy_agent(
                item_id=request.item_id,
                agent_type=agent_type,
                changed_files=changed_files,
                timeout_ms=timeout_ms,
            )
            agent_reports.append(report)

            # Log progress
            status = report.get("status", "unknown")
            issue_count = len(report.get("issues", []))
            if status == "complete":
                print_info(f"  {agent_type.value}: {issue_count} issues found")
            elif status == "timeout":
                print_warning(f"  {agent_type.value}: timed out")
            else:
                print_error(f"  {agent_type.value}: {status}")

        total_issues = sum(len(r.get("issues", [])) for r in agent_reports)
        logger.info(f"Review complete: {len(agent_reports)} agents, {total_issues} total issues")

        return {
            "item_id": request.item_id,
            "agent_reports": agent_reports,
            "total_issues": total_issues,
        }

    def _deploy_agent(
        self,
        item_id: str,
        agent_type: AgentType,
        changed_files: list[str] | None,
        timeout_ms: int = 60000,
    ) -> dict[str, Any]:
        """Deploy a review agent using AgentDeployer.

        Args:
            item_id: Plan item ID being reviewed
            agent_type: Type of review agent
            timeout_ms: Timeout in milliseconds

        Returns:
            Agent report dictionary
        """
        logger.debug(f"Deploying {agent_type.value} agent for {item_id}")

        # Use the deployer to run the agent
        result = self._deployer.run_agent(
            agent_type=agent_type,
            item_id=item_id,
            changed_files=changed_files,
            timeout_ms=timeout_ms,
        )

        # Convert AgentResult to dict for API serialization
        report = result.to_dict()
        report["item_id"] = item_id

        return report

    def _get_changed_files(self) -> list[str] | None:
        """Collect changed files from git status when available."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self._working_dir,
                check=False,
                capture_output=True,
                text=True,
                timeout=2,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

        if result.returncode != 0:
            return None

        files: list[str] = []
        for line in result.stdout.splitlines():
            if not line:
                continue
            path = line[3:]
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            files.append(path)

        return files or None


__all__ = ["ReviewHandler"]
