"""Client-side agent deployment and execution.

This module provides infrastructure for deploying and managing review agents
for the Hybrid Orchestration architecture. Agents run on the client and analyze
code for quality, security, testing, and documentation issues.

Key Components:
    - AgentDeployer: Manages subprocess-based agent deployment
    - AgentRegistry: Registry of available agent types
    - Concrete agent implementations (ClaudeCode, Security, Testing, Docs, CodeQuality)

Protocol Flow (from PRD Section 2):
    1. Server sends ReviewRequest with agents_to_run
    2. Client deploys specified agents via AgentDeployer
    3. Each agent analyzes code and returns AgentReport
    4. AgentDeployer collects reports and returns to orchestrator

Example:
    >>> from obra.agents import AgentDeployer, AgentRegistry
    >>> deployer = AgentDeployer(Path("/workspace"))
    >>> reports = deployer.run_agents(
    ...     agents=["security", "testing"],
    ...     item_id="T1",
    ...     timeout_ms=60000
    ... )

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md Section 2
    - obra/hybrid/handlers/review.py
    - obra/api/protocol.py
"""

from obra.agents.base import AgentResult, BaseAgent
from obra.agents.claude_code import ClaudeCodeAgent
from obra.agents.code_quality import CodeQualityAgent
from obra.agents.deployer import AgentDeployer
from obra.agents.docs import DocsAgent
from obra.agents.registry import AgentRegistry, get_registry
from obra.agents.security import SecurityAgent
from obra.agents.testing import TestingAgent

__all__ = [
    # Core infrastructure
    "AgentDeployer",
    "AgentRegistry",
    "get_registry",
    # Base classes
    "BaseAgent",
    "AgentResult",
    # Concrete agents
    "ClaudeCodeAgent",
    "SecurityAgent",
    "TestingAgent",
    "DocsAgent",
    "CodeQualityAgent",
]
