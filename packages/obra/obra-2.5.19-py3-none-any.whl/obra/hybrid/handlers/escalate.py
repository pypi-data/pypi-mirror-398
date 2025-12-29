"""Escalate handler for Hybrid Orchestrator.

This module handles the ESCALATE action from the server. It displays escalation
notices to the user and collects their decision on how to proceed.

The escalation process:
    1. Receive EscalationNotice with reason and blocking issues
    2. Display escalation information to user
    3. Present available options
    4. Collect and return user decision

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md Section 2
    - obra/api/protocol.py
    - obra/hybrid/orchestrator.py
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from obra.api.protocol import (
    EscalationNotice,
    EscalationReason,
    UserDecisionChoice,
)
from obra.display import (
    console,
    create_table,
    print_info,
    print_panel,
    print_warning,
)

logger = logging.getLogger(__name__)


class EscalateHandler:
    """Handler for ESCALATE action.

    Displays escalation notices and collects user decisions. In interactive mode,
    prompts the user for input. In non-interactive mode, uses the default decision
    or a provided callback.

    Example:
        >>> handler = EscalateHandler(Path("/path/to/project"))
        >>> notice = EscalationNotice(
        ...     escalation_id="esc-001",
        ...     reason=EscalationReason.MAX_ITERATIONS,
        ...     blocking_issues=[{"description": "Oscillating fix"}]
        ... )
        >>> result = handler.handle(notice)
        >>> print(result["decision"])
    """

    # Maps escalation reasons to human-readable titles
    REASON_TITLES = {
        EscalationReason.MAX_ITERATIONS: "Maximum Iterations Reached",
        EscalationReason.OSCILLATION: "Oscillation Detected",
        EscalationReason.USER_REQUESTED: "User Requested Escalation",
        EscalationReason.BLOCKED: "Progress Blocked",
    }

    # Maps escalation reasons to detailed explanations
    REASON_EXPLANATIONS = {
        EscalationReason.MAX_ITERATIONS: (
            "The refinement loop has reached the maximum number of iterations "
            "without resolving all blocking issues. This may indicate the issues "
            "require human intervention or architectural changes."
        ),
        EscalationReason.OSCILLATION: (
            "The system has detected oscillating behavior where the same issues "
            "keep recurring across iterations. This typically indicates conflicting "
            "requirements or constraints that need human resolution."
        ),
        EscalationReason.USER_REQUESTED: (
            "You requested to escalate this session for manual review."
        ),
        EscalationReason.BLOCKED: (
            "Progress has been blocked due to unresolvable issues. These issues "
            "may require access to resources or knowledge not available to the system."
        ),
    }

    # Maps decision choices to descriptions
    DECISION_DESCRIPTIONS = {
        UserDecisionChoice.FORCE_COMPLETE: (
            "Accept current state and complete the session. Blocking issues "
            "will be logged but not resolved."
        ),
        UserDecisionChoice.CONTINUE_FIXING: (
            "Continue attempting to fix issues for additional iterations."
        ),
        UserDecisionChoice.ABANDON: (
            "Abandon the session without completing. All progress will be lost."
        ),
    }

    def __init__(
        self,
        working_dir: Path,
        decision_callback: Callable[[EscalationNotice], UserDecisionChoice] | None = None,
        interactive: bool = True,
    ) -> None:
        """Initialize EscalateHandler.

        Args:
            working_dir: Working directory for file access
            decision_callback: Optional callback for automated decision making
            interactive: Whether to prompt user interactively
        """
        self._working_dir = working_dir
        self._decision_callback = decision_callback
        self._interactive = interactive

    def handle(self, notice: EscalationNotice) -> dict[str, Any]:
        """Handle ESCALATE action.

        Args:
            notice: EscalationNotice from server

        Returns:
            Dict with escalation_id, decision, and reason
        """
        logger.info(f"Handling escalation: {notice.escalation_id} ({notice.reason.value})")

        # Display escalation information
        self._display_escalation(notice)

        # Get user decision
        if self._decision_callback:
            decision = self._decision_callback(notice)
            reason = "Decision provided by callback"
        elif self._interactive:
            decision, reason = self._prompt_user(notice)
        else:
            # Non-interactive mode: default to force complete
            decision = UserDecisionChoice.FORCE_COMPLETE
            reason = "Auto-completed (non-interactive mode)"
            print_info(f"Non-interactive mode: defaulting to {decision.value}")

        logger.info(f"Escalation decision: {decision.value}")

        return {
            "escalation_id": notice.escalation_id,
            "decision": decision.value,
            "reason": reason,
        }

    def _display_escalation(self, notice: EscalationNotice) -> None:
        """Display escalation information to user.

        Args:
            notice: EscalationNotice to display
        """
        # Display header panel
        title = self.REASON_TITLES.get(notice.reason, "Escalation Required")
        explanation = self.REASON_EXPLANATIONS.get(notice.reason, "")

        print_panel(
            f"{explanation}\n\nEscalation ID: {notice.escalation_id}",
            title=title,
            style="yellow",
        )

        # Display blocking issues
        if notice.blocking_issues:
            self._display_blocking_issues(notice.blocking_issues)

        # Display iteration history if available
        if notice.iteration_history:
            self._display_iteration_history(notice.iteration_history)

    def _display_blocking_issues(self, issues: list[dict[str, Any]]) -> None:
        """Display blocking issues table.

        Args:
            issues: List of blocking issues
        """
        table = create_table(title="Blocking Issues", show_header=True)
        table.add_column("ID", style="cyan", width=12)
        table.add_column("Priority", style="yellow", width=8)
        table.add_column("Description", style="white")

        for issue in issues[:10]:  # Show first 10 issues
            issue_id = issue.get("id", "N/A")
            priority = issue.get("priority", "P3")
            description = issue.get("description", "No description")

            # Truncate long descriptions
            if len(description) > 60:
                description = description[:57] + "..."

            table.add_row(issue_id, priority, description)

        console.print(table)

        if len(issues) > 10:
            print_info(f"  ... and {len(issues) - 10} more issues")

    def _display_iteration_history(self, history: list[dict[str, Any]]) -> None:
        """Display iteration history.

        Args:
            history: List of iteration summaries
        """
        table = create_table(title="Iteration History", show_header=True)
        table.add_column("Iteration", style="cyan", width=10)
        table.add_column("Action", style="blue", width=15)
        table.add_column("Result", style="white")

        for entry in history[-5:]:  # Show last 5 iterations
            iteration = str(entry.get("iteration", "?"))
            action = entry.get("action", "unknown")
            result = entry.get("result", "")

            # Truncate long results
            if len(result) > 50:
                result = result[:47] + "..."

            table.add_row(iteration, action, result)

        console.print(table)

    def _prompt_user(self, notice: EscalationNotice) -> tuple[UserDecisionChoice, str]:
        """Prompt user for decision.

        Args:
            notice: EscalationNotice

        Returns:
            Tuple of (decision, reason)
        """
        # Display options
        console.print("\n[bold]Available Options:[/bold]")

        options = notice.options if notice.options else [
            {"choice": "force_complete", "label": "Force Complete"},
            {"choice": "continue_fixing", "label": "Continue Fixing"},
            {"choice": "abandon", "label": "Abandon Session"},
        ]

        for i, opt in enumerate(options, 1):
            choice = opt.get("choice", "")
            label = opt.get("label", choice)
            try:
                decision_choice = UserDecisionChoice(choice)
                description = self.DECISION_DESCRIPTIONS.get(decision_choice, "")
            except ValueError:
                description = opt.get("description", "")

            console.print(f"  {i}. [cyan]{label}[/cyan]")
            if description:
                console.print(f"     [dim]{description}[/dim]")

        # In headless/automated mode, don't prompt - return default
        # Check for common indicators of non-interactive environment
        import os
        import sys

        is_headless = (
            not sys.stdin.isatty()
            or os.environ.get("OBRA_HEADLESS") == "1"
            or os.environ.get("CI") == "true"
        )

        if is_headless:
            print_warning("Non-interactive environment detected, using default decision")
            return UserDecisionChoice.FORCE_COMPLETE, "Auto-completed (headless mode)"

        # Prompt for choice
        console.print("\n[bold]Enter your choice (1-3):[/bold] ", end="")

        try:
            choice_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            print_warning("\nInput cancelled, using default decision")
            return UserDecisionChoice.FORCE_COMPLETE, "Input cancelled"

        # Parse choice
        try:
            choice_num = int(choice_input)
            if 1 <= choice_num <= len(options):
                selected = options[choice_num - 1]
                choice_str = selected.get("choice", "force_complete")
                decision = UserDecisionChoice(choice_str)
            else:
                print_warning(f"Invalid choice {choice_num}, defaulting to force complete")
                decision = UserDecisionChoice.FORCE_COMPLETE
        except (ValueError, KeyError):
            print_warning(f"Invalid input '{choice_input}', defaulting to force complete")
            decision = UserDecisionChoice.FORCE_COMPLETE

        # Optionally get reason
        reason = ""
        if decision in (UserDecisionChoice.FORCE_COMPLETE, UserDecisionChoice.ABANDON):
            console.print("[dim]Reason (optional, press Enter to skip):[/dim] ", end="")
            try:
                reason = input().strip()
            except (EOFError, KeyboardInterrupt):
                pass

        return decision, reason


__all__ = ["EscalateHandler"]
