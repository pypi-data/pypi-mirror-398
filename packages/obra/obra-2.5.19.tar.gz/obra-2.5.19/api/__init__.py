"""API client module for Obra.

Provides HTTP client wrapper for communicating with Cloud Functions endpoints,
implementing retry logic, timeout handling, and optional compression.

Also provides protocol types for the hybrid architecture message passing.

Example:
    from obra.api import APIClient
    from obra.api.protocol import ServerAction, DeriveRequest

    client = APIClient.from_config()
    response = client.orchestrate(
        user_id="user123",
        project_id="proj456",
        working_dir="/home/user/project",
        objective="Add user authentication"
    )
"""

from obra.api.client import APIClient
from obra.api.protocol import (
    ActionType,
    AgentReport,
    AgentType,
    CompletionNotice,
    DerivedPlan,
    DeriveRequest,
    EscalationNotice,
    EscalationReason,
    ExaminationReport,
    ExamineRequest,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    FixRequest,
    FixResult,
    Priority,
    ResumeContext,
    ReviewRequest,
    RevisedPlan,
    RevisionRequest,
    ServerAction,
    SessionPhase,
    SessionStart,
    SessionStatus,
    UserDecision,
    UserDecisionChoice,
)

__all__ = [
    # Client
    "APIClient",
    # Enums
    "ActionType",
    "SessionPhase",
    "SessionStatus",
    "Priority",
    "ExecutionStatus",
    "AgentType",
    "EscalationReason",
    "UserDecisionChoice",
    # Server -> Client
    "ServerAction",
    "DeriveRequest",
    "ExamineRequest",
    "RevisionRequest",
    "ExecutionRequest",
    "ReviewRequest",
    "FixRequest",
    "EscalationNotice",
    "CompletionNotice",
    # Client -> Server
    "SessionStart",
    "DerivedPlan",
    "ExaminationReport",
    "RevisedPlan",
    "ExecutionResult",
    "AgentReport",
    "FixResult",
    "UserDecision",
    # Resume
    "ResumeContext",
]
