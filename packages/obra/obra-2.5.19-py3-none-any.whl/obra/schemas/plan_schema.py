"""Pydantic schemas for machine plan validation.

This module provides unified schema-based validation for MACHINE_PLAN
files (JSON/YAML format). Replaces the multi-layer patch stack with
strict Pydantic validation.

Architecture:
    - TaskSchema: Individual task validation
    - StorySchema: Story with tasks
    - MachinePlanSchema: Complete plan structure

Related:
    - docs/design/briefs/PLAN_VALIDATION_ARCHITECTURE_REDESIGN_BRIEF.md
    - docs/decisions/ADR-022-derivative-plan-architecture.md
    - obra/validation/plan_validator.py (uses these schemas)

Feature Flag:
    - config key: derivation.plan_validation.use_pydantic
    - v2.2.0: default false (shadow mode)
    - v2.2.1: default true (Pydantic primary)
    - v2.3.0: remove flag and legacy validator
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class TaskSchema(BaseModel):
    """Pydantic schema for task validation.

    Validates individual task structure with strict constraints.

    Attributes:
        id: Task identifier (format: S<N>.T<M>, e.g., "S1.T1")
        desc: Task description (non-empty string)
        status: Task status (pending, in_progress, completed, blocked)
        verify: Verification criteria (non-empty string)
        depends_on: Optional list of task IDs this depends on
        notes: Optional notes about task progress or blockers

    Example:
        >>> task = TaskSchema(
        ...     id="S1.T1",
        ...     desc="Create schema file",
        ...     status="pending",
        ...     verify="File exists and imports successfully"
        ... )
    """

    id: str = Field(
        ...,
        pattern=r"^S\d+\.T\d+$",
        description="Task ID in format S<N>.T<M>",
    )
    desc: str = Field(
        ...,
        min_length=1,
        description="Task description (non-empty)",
    )
    status: Literal["pending", "in_progress", "completed", "blocked"] = Field(
        ...,
        description="Current task status",
    )
    verify: str = Field(
        ...,
        min_length=1,
        description="Verification criteria for task completion",
    )
    depends_on: list[str] | None = Field(
        default=None,
        description="Optional list of task IDs this task depends on",
    )
    notes: str | None = Field(
        default=None,
        description="Optional notes about task progress or blockers",
    )

    @field_validator("depends_on")
    @classmethod
    def validate_depends_on(cls, v: list[str] | None) -> list[str] | None:
        """Validate dependency task IDs match expected format."""
        if v is None:
            return None

        import re

        pattern = re.compile(r"^S\d+\.T\d+$")
        for dep_id in v:
            if not pattern.match(dep_id):
                raise ValueError(
                    f"Dependency ID '{dep_id}' must match format S<N>.T<M>"
                )

        return v

    model_config = {"extra": "forbid"}


class StorySchema(BaseModel):
    """Pydantic schema for story validation.

    Validates story structure with nested tasks.

    Attributes:
        id: Story identifier (format: S<N>, e.g., "S1")
        title: Story title (non-empty string)
        status: Story status (pending, in_progress, completed, blocked)
        tasks: List of tasks in this story (at least one)
        pre_story_context: Optional context to read before starting story
        notes: Optional notes about story progress

    Example:
        >>> story = StorySchema(
        ...     id="S1",
        ...     title="Pydantic Schema Validator",
        ...     status="pending",
        ...     tasks=[task1, task2]
        ... )
    """

    id: str = Field(
        ...,
        pattern=r"^S\d+$",
        description="Story ID in format S<N>",
    )
    title: str = Field(
        ...,
        min_length=1,
        description="Story title (non-empty)",
    )
    status: Literal["pending", "in_progress", "completed", "blocked"] = Field(
        ...,
        description="Current story status",
    )
    tasks: list[TaskSchema] = Field(
        ...,
        min_length=1,
        description="List of tasks (at least one required)",
    )
    pre_story_context: str | None = Field(
        default=None,
        description="Optional context to read before starting story",
    )
    notes: str | None = Field(
        default=None,
        description="Optional notes about story progress",
    )

    @model_validator(mode="after")
    def validate_task_ids(self) -> "StorySchema":
        """Ensure all task IDs belong to this story."""
        story_id = self.id
        for task in self.tasks:
            if not task.id.startswith(f"{story_id}.T"):
                raise ValueError(
                    f"Task ID '{task.id}' does not belong to story '{story_id}'. "
                    f"Expected format: {story_id}.T<N>"
                )

        return self

    model_config = {"extra": "forbid"}


class MachinePlanSchema(BaseModel):
    """Pydantic schema for complete machine plan validation.

    Validates the entire MACHINE_PLAN structure with all stories,
    tasks, and metadata.

    Attributes:
        work_id: Work identifier (format: FEAT-XXX-001, EPIC-XXX-001, etc.)
        stories: List of stories (at least one)
        completion_checklist: List of completion criteria (strings, not lists!)
        version: Optional plan version number
        created: Optional creation timestamp (ISO-8601)
        last_updated: Optional last update timestamp (ISO-8601)
        context: Optional context metadata (key_files, related_docs, assumptions)
        flags: Optional feature flags (breaking_changes, performance_testing, etc.)

    CRITICAL: completion_checklist items must be strings, not nested lists.
        ✓ Correct: ["All tests pass", "Docs updated"]
        ✗ Wrong: [["[ ]", "All tests pass"], ["[ ]", "Docs updated"]]

    Example:
        >>> plan = MachinePlanSchema(
        ...     work_id="FEAT-VALIDATION-001",
        ...     stories=[story1, story2],
        ...     completion_checklist=["All tests pass", "Docs updated"]
        ... )
    """

    work_id: str = Field(
        ...,
        pattern=r"^[A-Z]+-[A-Z-]+(-\d{3})?$",
        description="Work ID in format PREFIX-NAME or PREFIX-NAME-NNN (e.g., FEAT-VALIDATION-001, CHORE-CONFIG-INVESTIGATION)",
    )
    stories: list[StorySchema] = Field(
        ...,
        min_length=1,
        description="List of stories (at least one required)",
    )
    completion_checklist: list[str] = Field(
        ...,
        description="Completion criteria as strings (not lists!)",
    )
    version: float | None = Field(
        default=None,
        description="Optional plan version number",
    )
    created: str | None = Field(
        default=None,
        description="Optional creation timestamp (ISO-8601 format)",
    )
    last_updated: str | None = Field(
        default=None,
        description="Optional last update timestamp (ISO-8601 format)",
    )
    context: dict[str, Any] | None = Field(
        default=None,
        description="Optional context metadata",
    )
    flags: dict[str, Any] | None = Field(
        default=None,
        description="Optional feature flags and metadata",
    )

    @field_validator("completion_checklist")
    @classmethod
    def validate_completion_checklist(cls, v: list[str]) -> list[str]:
        """Ensure checklist items are strings, not nested lists.

        Common error: YAML parsing of "- [ ] Item" creates nested lists.
        This validator catches that pattern and provides a clear error.
        """
        if not v:
            raise ValueError("completion_checklist cannot be empty")

        for i, item in enumerate(v):
            if not isinstance(item, str):
                # Detect nested list pattern from YAML checkbox ambiguity
                if isinstance(item, list):
                    raise ValueError(
                        f"completion_checklist[{i}] is a list, not a string. "
                        f"Got: {item}. "
                        f"YAML checkbox patterns like '- [ ] Item' must be quoted: '- \"[ ] Item\"'. "
                        f"See docs/guides/migration/plan-validation-v2-migration.md for fixes."
                    )
                raise ValueError(
                    f"completion_checklist[{i}] must be a string, got {type(item).__name__}: {item}"
                )

        return v

    @model_validator(mode="after")
    def validate_story_ids(self) -> "MachinePlanSchema":
        """Ensure story IDs are sequential and unique.

        Stories can start from S0 or S1, but must be sequential.
        """
        if not self.stories:
            return self

        # Extract starting index from first story (allow S0 or S1)
        first_id = self.stories[0].id
        if not first_id.startswith("S"):
            raise ValueError(f"Story IDs must start with 'S', got: {first_id}")

        try:
            start_idx = int(first_id[1:])
        except ValueError:
            raise ValueError(f"Invalid story ID format: {first_id}")

        # Allow starting from S0 or S1 for backward compatibility
        if start_idx not in (0, 1):
            raise ValueError(
                f"Story IDs must start from S0 or S1, got: {first_id}"
            )

        seen_ids = set()
        for i, story in enumerate(self.stories):
            expected_id = f"S{start_idx + i}"
            if story.id != expected_id:
                raise ValueError(
                    f"Story ID mismatch at index {i}: expected '{expected_id}', got '{story.id}'. "
                    f"Story IDs must be sequential starting from S{start_idx}."
                )

            if story.id in seen_ids:
                raise ValueError(f"Duplicate story ID: {story.id}")

            seen_ids.add(story.id)

        return self

    model_config = {"extra": "forbid"}


# Convenience exports
__all__ = [
    "MachinePlanSchema",
    "StorySchema",
    "TaskSchema",
]
