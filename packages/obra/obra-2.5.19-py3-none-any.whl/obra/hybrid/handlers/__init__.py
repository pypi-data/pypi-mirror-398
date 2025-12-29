"""Action handlers for Hybrid Orchestrator.

This module provides handlers for each action type in the hybrid architecture.
Each handler is responsible for processing a specific server action and
returning results to report back to the server.

Handlers:
    - DeriveHandler: Derives implementation plan from objective
    - ExamineHandler: Examines plan using LLM
    - ReviseHandler: Revises plan based on issues
    - ExecuteHandler: Executes plan items
    - ReviewHandler: Runs review agents on executed code
    - FixHandler: Fixes issues found during review
    - EscalateHandler: Handles escalation notices and user decisions

Related:
    - obra/hybrid/orchestrator.py
    - obra/api/protocol.py
"""

from obra.hybrid.handlers.derive import DeriveHandler
from obra.hybrid.handlers.escalate import EscalateHandler
from obra.hybrid.handlers.examine import ExamineHandler
from obra.hybrid.handlers.execute import ExecuteHandler
from obra.hybrid.handlers.fix import FixHandler
from obra.hybrid.handlers.review import ReviewHandler
from obra.hybrid.handlers.revise import ReviseHandler

__all__ = [
    "DeriveHandler",
    "EscalateHandler",
    "ExamineHandler",
    "ExecuteHandler",
    "FixHandler",
    "ReviewHandler",
    "ReviseHandler",
]
