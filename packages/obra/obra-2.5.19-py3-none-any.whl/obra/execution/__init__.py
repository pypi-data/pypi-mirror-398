"""Execution engines for plan derivation and revision.

This package provides client-side execution engines that interface with
the hybrid orchestration architecture:

- DerivationEngine: Breaks down objectives into implementation plans
- RevisionEngine: Revises plans based on examination feedback

These engines use LLM invocation to perform their work locally while
the server manages orchestration decisions.

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md
    - obra/hybrid/orchestrator.py
    - obra/llm/invoker.py
"""

from obra.execution.derivation import DerivationEngine, DerivationResult
from obra.execution.revision import RevisionEngine, RevisionResult

__all__ = [
    "DerivationEngine",
    "DerivationResult",
    "RevisionEngine",
    "RevisionResult",
]
