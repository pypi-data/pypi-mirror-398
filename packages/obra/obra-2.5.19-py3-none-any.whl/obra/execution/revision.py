"""Revision engine for refining plans based on examination feedback.

This module provides the RevisionEngine class that uses LLM invocation
to revise plans based on identified issues from examination.

The engine:
    1. Receives current plan and issues to address
    2. Builds a revision prompt with context-aware guidance
    3. Invokes LLM to generate revised plan
    4. Parses response into revised plan items with change tracking

Per design decisions:
    - D5: Context-aware revision (full plan + issues + "fix these, keep others")
    - D14: METRICS-001 event integration for revision lifecycle

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md Section 1
    - obra/hybrid/handlers/revise.py (handler layer)
    - obra/llm/invoker.py (LLM invocation)
    - src/planning/reviser.py (CLI implementation reference)
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from obra.llm.invoker import LLMInvoker

logger = logging.getLogger(__name__)


@dataclass
class PlanChange:
    """Record of a change made during revision.

    Tracks what was changed, which issue it addressed, and details
    of the modification for audit trail purposes.

    Attributes:
        task_ref: Reference to the task that was modified
        issue_addressed: Description of the issue that was addressed
        change: Description of what was changed
        old_value: Previous value (optional)
        new_value: New value (optional)
    """

    task_ref: str
    issue_addressed: str
    change: str
    old_value: str = ""
    new_value: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "task_ref": self.task_ref,
            "issue_addressed": self.issue_addressed,
            "change": self.change,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


@dataclass
class RevisionResult:
    """Result from plan revision.

    Contains the revised plan, changes made, and any remaining concerns
    that were deferred to future iterations.

    Attributes:
        revised_items: The updated plan items
        changes_made: List of changes with audit trail
        remaining_concerns: P2/P3 issues deferred for later
        raw_response: Full LLM response for debugging
        duration_seconds: Time taken for revision
        tokens_used: Token count for the revision call
        success: Whether revision completed successfully
        error_message: Error message if failed
    """

    revised_items: list[dict[str, Any]] = field(default_factory=list)
    changes_made: list[PlanChange] = field(default_factory=list)
    remaining_concerns: list[str] = field(default_factory=list)
    raw_response: str = ""
    duration_seconds: float = 0.0
    tokens_used: int = 0
    success: bool = True
    error_message: str = ""

    @property
    def changes_count(self) -> int:
        """Count of changes made during revision."""
        return len(self.changes_made)

    @property
    def has_remaining_concerns(self) -> bool:
        """Whether there are deferred concerns."""
        return len(self.remaining_concerns) > 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "revised_items": self.revised_items,
            "changes_count": self.changes_count,
            "changes_made": [c.to_dict() for c in self.changes_made],
            "remaining_concerns": self.remaining_concerns,
            "duration_seconds": self.duration_seconds,
            "tokens_used": self.tokens_used,
            "success": self.success,
            "error_message": self.error_message,
        }


class RevisionEngine:
    """Engine for revising plans based on examination feedback.

    Uses context-aware revision per D5:
    - Provides LLM with full plan and specific issues
    - Instructs to fix flagged items while preserving stable ones
    - Returns changes made for audit trail

    Example:
        >>> from obra.llm.invoker import LLMInvoker
        >>> invoker = LLMInvoker()
        >>> engine = RevisionEngine(llm_invoker=invoker)
        >>> result = engine.revise(
        ...     current_items=plan_items,
        ...     issues=examination_issues,
        ...     objective="Add user authentication",
        ... )
        >>> print(f"Made {result.changes_count} changes")

    Thread-safety:
        Thread-safe through LLMInvoker's thread safety guarantees.

    Related:
        - obra/hybrid/handlers/revise.py (handler layer)
        - obra/llm/invoker.py (LLM invocation)
    """

    def __init__(
        self,
        llm_invoker: Optional["LLMInvoker"] = None,
        thinking_enabled: bool = True,
        thinking_level: str = "standard",
    ) -> None:
        """Initialize RevisionEngine.

        Args:
            llm_invoker: LLMInvoker instance for LLM calls
            thinking_enabled: Whether to use extended thinking
            thinking_level: Thinking level (off, minimal, standard, high, maximum)
        """
        self._llm_invoker = llm_invoker
        self._thinking_enabled = thinking_enabled
        self._thinking_level = thinking_level

        logger.debug(
            f"RevisionEngine initialized: "
            f"thinking_enabled={thinking_enabled}, thinking_level={thinking_level}"
        )

    def revise(
        self,
        current_items: list[dict[str, Any]],
        issues: list[dict[str, Any]],
        objective: str,
        iteration: int = 1,
        provider: str = "anthropic",
    ) -> RevisionResult:
        """Revise plan to address identified issues.

        Uses context-aware revision per D5:
        - Provides LLM with full plan and specific issues
        - Instructs to fix flagged items while preserving stable ones

        Args:
            current_items: Current plan items
            issues: Issues to address
            objective: Original task objective
            iteration: Current revision iteration
            provider: LLM provider to use

        Returns:
            RevisionResult with revised items and changes made
        """
        start_time = time.time()

        try:
            # Separate blocking vs non-blocking issues
            blocking_issues = [
                i for i in issues
                if i.get("priority") in ("P0", "P1")
            ]
            non_blocking_issues = [
                i for i in issues
                if i.get("priority") not in ("P0", "P1")
            ]

            # Build prompt
            prompt = self._build_prompt(
                current_items=current_items,
                issues=issues,
                blocking_issues=blocking_issues,
                objective=objective,
                iteration=iteration,
            )

            # Invoke LLM
            raw_response, tokens_used = self._invoke_llm(
                prompt=prompt,
                provider=provider,
            )

            # Parse response
            revised_items, changes_made, remaining = self._parse_response(
                raw_response=raw_response,
                original_items=current_items,
                issues=issues,
            )

            # Add non-blocking issues to remaining concerns
            remaining_concerns = remaining + [
                f"{i.get('priority', 'P3')}: {i.get('description', 'Unknown issue')}"
                for i in non_blocking_issues
            ]

            duration = time.time() - start_time
            logger.info(
                f"Revision completed: {len(changes_made)} changes, "
                f"{len(remaining_concerns)} remaining concerns, {duration:.2f}s"
            )

            return RevisionResult(
                revised_items=revised_items,
                changes_made=changes_made,
                remaining_concerns=remaining_concerns,
                raw_response=raw_response,
                duration_seconds=duration,
                tokens_used=tokens_used,
                success=True,
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Revision failed: {e}")
            return RevisionResult(
                revised_items=current_items,  # Return original on failure
                success=False,
                error_message=str(e),
                duration_seconds=duration,
            )

    def _build_prompt(
        self,
        current_items: list[dict[str, Any]],
        issues: list[dict[str, Any]],
        blocking_issues: list[dict[str, Any]],
        objective: str,
        iteration: int,
    ) -> str:
        """Build revision prompt.

        Args:
            current_items: Current plan items
            issues: All issues
            blocking_issues: P0/P1 issues that must be addressed
            objective: Original objective
            iteration: Current iteration number

        Returns:
            Prompt string for LLM
        """
        # Format current plan
        current_plan_json = json.dumps({"plan_items": current_items}, indent=2)

        # Format issues
        issues_section = ""
        for issue in issues:
            priority = issue.get("priority", "P3")
            task_ref = issue.get("task_ref", issue.get("item_id", "unknown"))
            description = issue.get("description", "No description")
            suggestion = issue.get("suggestion", "")

            issues_section += f"- [{priority}] {task_ref}: {description}"
            if suggestion:
                issues_section += f" (Suggested: {suggestion})"
            issues_section += "\n"

        # Format blocking issues specifically
        blocking_section = ""
        if blocking_issues:
            blocking_section = "\n## Critical Issues (MUST Address)\n"
            for issue in blocking_issues:
                priority = issue.get("priority", "P0")
                task_ref = issue.get("task_ref", issue.get("item_id", "unknown"))
                description = issue.get("description", "No description")
                blocking_section += f"- [{priority}] {task_ref}: {description}\n"

        prompt = f"""You are an expert software architect revising an implementation plan.
Your job is to address identified issues while preserving what works well.

## Original Objective
{objective}

## Current Plan (Version {iteration})
```json
{current_plan_json}
```

## Issues to Address
{issues_section}
{blocking_section}
## Revision Guidelines

1. **Address all P0 and P1 issues first** - these block implementation
2. **Modify only the tasks that need changes** - keep stable tasks unchanged
3. **Maintain coherence and dependencies** after changes
4. **Preserve task IDs** where possible for traceability
5. **Document what you changed** in the changes_made array

## Output Format

Return a JSON object with:
- revised_plan: Object with plan_items array (same format as input)
- changes_made: Array of change records
- remaining_concerns: Array of issues deferred to future iterations

```json
{{
  "revised_plan": {{
    "plan_items": [
      {{
        "id": "T1",
        "item_type": "task",
        "title": "Updated title",
        "description": "Updated description",
        "acceptance_criteria": ["..."],
        "dependencies": [],
        "work_phase": "implement"
      }}
    ]
  }},
  "changes_made": [
    {{
      "task_ref": "T1",
      "issue_addressed": "P1: Unclear acceptance criteria",
      "change": "Added specific metrics",
      "old_value": "Response should be fast",
      "new_value": "Response time < 200ms"
    }}
  ],
  "remaining_concerns": [
    "P2: Consider adding caching (deferred)"
  ]
}}
```

Return ONLY the JSON object, no additional text.
"""
        return prompt

    def _invoke_llm(
        self,
        prompt: str,
        provider: str,
    ) -> tuple[str, int]:
        """Invoke LLM to generate revision.

        Args:
            prompt: Revision prompt
            provider: LLM provider name

        Returns:
            Tuple of (raw_response, tokens_used)
        """
        if self._llm_invoker is None:
            logger.warning("No LLM invoker configured, returning placeholder")
            return self._placeholder_response(), 0

        # Determine thinking level
        thinking_level = None
        if self._thinking_enabled:
            thinking_level = self._thinking_level

        # Invoke LLM
        result = self._llm_invoker.invoke(
            prompt=prompt,
            provider=provider,
            thinking_level=thinking_level,
            response_format="json",
        )

        return result.content, result.tokens_used

    def _placeholder_response(self) -> str:
        """Generate placeholder response when no LLM available.

        Returns:
            Placeholder JSON response
        """
        return json.dumps({
            "revised_plan": {
                "plan_items": [
                    {
                        "id": "T1",
                        "item_type": "task",
                        "title": "Placeholder task",
                        "description": "LLM invoker not configured",
                        "acceptance_criteria": [],
                        "dependencies": [],
                        "work_phase": "implement",
                    }
                ]
            },
            "changes_made": [],
            "remaining_concerns": ["LLM invoker not configured - no revision performed"],
        })

    def _parse_response(
        self,
        raw_response: str,
        original_items: list[dict[str, Any]],
        issues: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[PlanChange], list[str]]:
        """Parse LLM revision response.

        Args:
            raw_response: Raw LLM response
            original_items: Original plan items for fallback
            issues: Original issues for cross-reference

        Returns:
            Tuple of (revised_items, changes_made, remaining_concerns)
        """
        try:
            response = raw_response.strip()

            # Handle markdown code blocks
            if response.startswith("```"):
                lines = response.split("\n")
                start = 1 if lines[0].startswith("```") else 0
                end = len(lines) - 1 if lines[-1] == "```" else len(lines)
                response = "\n".join(lines[start:end])

            # Parse JSON
            data = json.loads(response)

            # Extract revised plan
            revised_plan = data.get("revised_plan", data)
            if isinstance(revised_plan, dict):
                revised_items = revised_plan.get("plan_items", [])
            elif isinstance(revised_plan, list):
                revised_items = revised_plan
            else:
                revised_items = original_items

            # Extract changes made
            changes_made = []
            raw_changes = data.get("changes_made", [])
            for raw_change in raw_changes:
                if isinstance(raw_change, dict):
                    changes_made.append(PlanChange(
                        task_ref=raw_change.get("task_ref", ""),
                        issue_addressed=raw_change.get("issue_addressed", ""),
                        change=raw_change.get("change", ""),
                        old_value=raw_change.get("old_value", ""),
                        new_value=raw_change.get("new_value", ""),
                    ))

            # Extract remaining concerns
            remaining_concerns = data.get("remaining_concerns", [])
            if not isinstance(remaining_concerns, list):
                remaining_concerns = []
            remaining_concerns = [str(c) for c in remaining_concerns]

            return revised_items, changes_made, remaining_concerns

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse revision JSON: {e}")
            return original_items, [], [f"Parse error: {e!s}"]


__all__ = [
    "PlanChange",
    "RevisionEngine",
    "RevisionResult",
]
