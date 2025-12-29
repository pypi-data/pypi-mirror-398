"""Pydantic v2 base schemas for Obra API.

This module provides base Pydantic models with standard configuration
for API request/response validation in the Hybrid Architecture.

Architecture:
    - BaseAPIModel: Base model with common configuration
    - Request/Response models inherit from BaseAPIModel
    - Strict validation with no extra fields allowed
    - Serialization to camelCase for JavaScript interop

Usage:
    >>> from obra.api.schemas import BaseAPIModel
    >>> class MyRequest(BaseAPIModel):
    ...     user_id: str
    ...     action_type: str

Related:
    - obra/api/protocol.py: Current dataclass-based protocol types
    - obra/schemas/plan_schema.py: Plan validation schemas
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md

Future:
    - Migration from dataclass protocol to Pydantic schemas
    - OpenAPI spec generation from schemas
    - Automatic request/response validation
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseAPIModel(BaseModel):
    """Base Pydantic model with standard configuration for Obra API.

    Configuration:
        - extra='forbid': Reject any extra fields not defined in schema
        - validate_assignment=True: Validate field values on assignment
        - str_strip_whitespace=True: Strip whitespace from string fields
        - use_enum_values=True: Use enum values instead of enum objects in serialization
        - populate_by_name=True: Allow field population by both name and alias

    Example:
        >>> class UserRequest(BaseAPIModel):
        ...     user_id: str
        ...     email: str
        ...
        >>> req = UserRequest(user_id="123", email=" user@example.com ")
        >>> req.email
        'user@example.com'
        >>> req.model_dump()
        {'user_id': '123', 'email': 'user@example.com'}
    """

    model_config = ConfigDict(
        # Validation strictness
        extra="forbid",  # No undeclared fields allowed
        validate_assignment=True,  # Re-validate on assignment
        # String handling
        str_strip_whitespace=True,  # Auto-strip whitespace
        # Enum handling
        use_enum_values=True,  # Serialize enums as values
        # Field aliases
        populate_by_name=True,  # Allow both name and alias
        # JSON schema
        json_schema_extra={
            "description": "Base API model with standard Obra configuration"
        },
    )

    def model_dump_api(self, **kwargs: Any) -> dict[str, Any]:
        """Dump model for API transmission with standard settings.

        This method provides a consistent serialization format for API
        communication, excluding None values and using aliases.

        Args:
            **kwargs: Additional arguments passed to model_dump()

        Returns:
            Dictionary representation suitable for API transmission

        Example:
            >>> class MyRequest(BaseAPIModel):
            ...     user_id: str
            ...     optional_field: str | None = None
            ...
            >>> req = MyRequest(user_id="123")
            >>> req.model_dump_api()
            {'user_id': '123'}
        """
        return self.model_dump(
            exclude_none=True,  # Omit None values
            by_alias=True,  # Use field aliases
            **kwargs,
        )


class BaseAPIRequest(BaseAPIModel):
    """Base class for API request models.

    All request models should inherit from this class to ensure
    consistent validation and serialization behavior.

    Example:
        >>> class DeriveRequest(BaseAPIRequest):
        ...     objective: str
        ...     context: dict[str, Any] | None = None
    """



class BaseAPIResponse(BaseAPIModel):
    """Base class for API response models.

    All response models should inherit from this class to ensure
    consistent validation and serialization behavior.

    Example:
        >>> class DeriveResponse(BaseAPIResponse):
        ...     session_id: str
        ...     plan_items: list[dict[str, Any]]
    """



class IssueItem(BaseAPIModel):
    """Structured issue item for review results.

    This schema prevents ISSUE-SAAS-009 type mismatches where the server
    returns issues as strings instead of structured dictionaries.

    Attributes:
        id: Unique identifier for the issue
        description: Human-readable description of the issue
        severity: Optional severity level (e.g., "critical", "high", "medium", "low")

    Example:
        >>> issue = IssueItem(
        ...     id="SEC-001",
        ...     description="SQL injection vulnerability in query builder",
        ...     severity="critical"
        ... )
        >>> issue.model_dump()
        {'id': 'SEC-001', 'description': 'SQL injection vulnerability in query builder', 'severity': 'critical'}
    """

    id: str = Field(..., description="Unique identifier for the issue")
    description: str = Field(..., description="Human-readable description of the issue")
    severity: str | None = Field(None, description="Severity level of the issue")


class ReviewResult(BaseAPIModel):
    """Review result containing structured issues.

    This schema ensures type safety for review agent results by using
    structured IssueItem objects instead of plain strings or untyped dicts.

    Attributes:
        issues: List of structured issues found during review
        agent_type: Optional agent type that generated this result
        status: Optional status of the review (e.g., "complete", "timeout", "error")

    Example:
        >>> result = ReviewResult(
        ...     issues=[
        ...         IssueItem(id="SEC-001", description="SQL injection", severity="critical"),
        ...         IssueItem(id="TEST-001", description="Missing tests", severity="high")
        ...     ],
        ...     agent_type="security",
        ...     status="complete"
        ... )
        >>> len(result.issues)
        2
    """

    issues: list[IssueItem] = Field(
        default_factory=list, description="List of structured issues found during review"
    )
    agent_type: str | None = Field(None, description="Agent type that generated this result")
    status: str | None = Field(None, description="Status of the review")


class FixRequest(BaseAPIRequest):
    """Request to fix issues found during review.

    Sent by server after AgentReport when issues need fixing.
    Matches protocol.FixRequest dataclass structure.

    Attributes:
        issues_to_fix: List of issues to fix
        execution_order: Order to fix issues (by ID)
        base_prompt: Optional base prompt from server (ADR-027 two-tier prompting)

    Example:
        >>> request = FixRequest(
        ...     issues_to_fix=[
        ...         {"id": "SEC-001", "description": "SQL injection", "severity": "critical"}
        ...     ],
        ...     execution_order=["SEC-001"],
        ...     base_prompt="Fix the security issues"
        ... )
        >>> len(request.issues_to_fix)
        1
    """

    issues_to_fix: list[dict[str, Any]] = Field(
        default_factory=list, description="List of issues to fix"
    )
    execution_order: list[str] = Field(
        default_factory=list, description="Order to fix issues (by ID)"
    )
    base_prompt: str | None = Field(None, description="Base prompt from server")


class ExecutionResult(BaseAPIResponse):
    """Report execution result to server.

    Sent by client after executing a plan item.
    Matches protocol.ExecutionResult dataclass structure.

    Attributes:
        session_id: Session identifier
        item_id: Plan item ID that was executed
        status: Execution status (success, failure, partial)
        summary: LLM-generated summary
        files_changed: Number of files changed
        tests_passed: Whether tests passed
        test_count: Number of tests run
        coverage_delta: Change in coverage percentage

    Example:
        >>> result = ExecutionResult(
        ...     session_id="sess_123",
        ...     item_id="item_1",
        ...     status="success",
        ...     summary="Implemented feature X",
        ...     files_changed=3,
        ...     tests_passed=True,
        ...     test_count=15,
        ...     coverage_delta=2.5
        ... )
        >>> result.status
        'success'
    """

    session_id: str = Field(..., description="Session identifier")
    item_id: str = Field(..., description="Plan item ID that was executed")
    status: str = Field(..., description="Execution status (success, failure, partial)")
    summary: str = Field(default="", description="LLM-generated summary")
    files_changed: int = Field(default=0, description="Number of files changed")
    tests_passed: bool = Field(default=False, description="Whether tests passed")
    test_count: int = Field(default=0, description="Number of tests run")
    coverage_delta: float = Field(default=0.0, description="Change in coverage percentage")


class DerivationResult(BaseAPIResponse):
    """Report derived plan to server.

    Sent by client after completing derivation.
    Matches protocol.DerivedPlan dataclass structure.

    Attributes:
        session_id: Session identifier
        plan_items: Derived plan items
        raw_response: Raw LLM response (for debugging)

    Example:
        >>> result = DerivationResult(
        ...     session_id="sess_123",
        ...     plan_items=[
        ...         {"id": "1", "description": "Set up database", "status": "pending"}
        ...     ],
        ...     raw_response="Here is the plan..."
        ... )
        >>> len(result.plan_items)
        1
    """

    session_id: str = Field(..., description="Session identifier")
    plan_items: list[dict[str, Any]] = Field(
        default_factory=list, description="Derived plan items"
    )
    raw_response: str = Field(default="", description="Raw LLM response (for debugging)")


class ServerActionSchema(BaseAPIResponse):
    """Action instruction from server to client.

    This is the Pydantic validation schema for ServerAction protocol type.
    Provides strict validation for server responses to prevent type mismatches
    and invalid action values (fixes C8 from hardening analysis).

    Attributes:
        action: Action type to perform (derive, examine, revise, execute, review, fix, complete, escalate, wait, error)
        session_id: Session identifier
        iteration: Current iteration number
        payload: Action-specific data
        metadata: Additional metadata
        bypass_modes_active: List of active bypass modes (for warnings)
        error_code: Error code if action is ERROR
        error_message: Error message if action is ERROR
        timestamp: ISO-8601 timestamp

    Example:
        >>> action = ServerActionSchema(
        ...     action="derive",
        ...     session_id="sess_123",
        ...     iteration=1,
        ...     payload={"objective": "Build feature X"}
        ... )
        >>> action.action
        'derive'
    """

    action: str = Field(..., description="Action type to perform")
    session_id: str = Field(..., description="Session identifier")
    iteration: int = Field(default=0, description="Current iteration number")
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Action-specific data"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    bypass_modes_active: list[str] = Field(
        default_factory=list, description="List of active bypass modes"
    )
    error_code: str | None = Field(None, description="Error code if action is ERROR")
    error_message: str | None = Field(None, description="Error message if action is ERROR")
    timestamp: str | None = Field(None, description="ISO-8601 timestamp")
    rationale: str | None = Field(None, description="Rationale for action (ISSUE-SAAS-023)")  # Server may include this


# Convenience exports
__all__ = [
    "BaseAPIModel",
    "BaseAPIRequest",
    "BaseAPIResponse",
    "DerivationResult",
    "ExecutionResult",
    "FixRequest",
    "IssueItem",
    "ReviewResult",
    "ServerActionSchema",
]
