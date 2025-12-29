"""Hybrid orchestration module for Obra.

This module provides the client-side orchestration for the Unified Hybrid Architecture.
The HybridOrchestrator connects to the server, receives action instructions, and
dispatches to appropriate handlers.

Design Principle:
    Server owns the brain (decisions) - Client owns the hands (execution)

Example:
    from obra.hybrid import HybridOrchestrator

    orchestrator = HybridOrchestrator.from_config()
    result = orchestrator.derive(
        "Add user authentication",
        working_dir=Path("/path/to/project")
    )
    print(f"Completed: {result.items_completed} items")

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md
    - obra/api/protocol.py
"""

from obra.exceptions import ConnectionError, OrchestratorError
from obra.hybrid.orchestrator import HybridOrchestrator

__all__ = [
    "ConnectionError",
    "HybridOrchestrator",
    "OrchestratorError",
]
