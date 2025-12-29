"""Base class and types for review agents.

This module defines the BaseAgent abstract class and AgentResult dataclass
that all review agents must implement.

Agent Architecture:
    - Agents are lightweight, stateless workers
    - Each agent runs as a subprocess for isolation
    - Agents analyze code and return structured results
    - Results include issues (with priority) and dimension scores

Related:
    - obra/agents/deployer.py
    - obra/api/protocol.py
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from obra.api.protocol import AgentType, Priority

logger = logging.getLogger(__name__)


# Files that should be excluded from most agent analysis
# These are infrastructure/config files, not application code
EXCLUDED_FILES = {
    # Pytest infrastructure
    "conftest.py",
    # Build/packaging
    "setup.py",
    "setup.cfg",
    "pyproject.toml",
    # Noxfile/tox
    "noxfile.py",
    "toxfile.py",
    # Type stubs
    "py.typed",
}

# Patterns for files that should be excluded (checked with fnmatch)
EXCLUDED_PATTERNS = [
    # Migration files
    "**/migrations/*.py",
    "**/alembic/versions/*.py",
    # Auto-generated
    "**/*_pb2.py",  # protobuf
    "**/*_pb2_grpc.py",
]


@dataclass
class AgentIssue:
    """Issue found by a review agent.

    Attributes:
        id: Unique issue identifier
        title: Short description of the issue
        description: Detailed description
        priority: Issue priority (P0-P3)
        file_path: File where issue was found (if applicable)
        line_number: Line number (if applicable)
        dimension: Quality dimension (security, testing, docs, maintainability)
        suggestion: Suggested fix
        metadata: Additional metadata
    """

    id: str
    title: str
    description: str
    priority: Priority
    file_path: str | None = None
    line_number: int | None = None
    dimension: str = ""
    suggestion: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "dimension": self.dimension,
            "suggestion": self.suggestion,
            "metadata": self.metadata,
        }


@dataclass
class AgentResult:
    """Result from agent execution.

    Attributes:
        agent_type: Type of agent that produced this result
        status: Execution status (complete, timeout, error)
        issues: List of issues found
        scores: Dimension scores (0.0 - 1.0)
        execution_time_ms: Time taken in milliseconds
        error: Error message if status is error
        metadata: Additional metadata
    """

    agent_type: AgentType
    status: str  # complete, timeout, error
    issues: list[AgentIssue] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    execution_time_ms: int = 0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        return {
            "agent_type": self.agent_type.value,
            "status": self.status,
            "issues": [issue.to_dict() for issue in self.issues],
            "scores": self.scores,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
            "metadata": self.metadata,
        }


class BaseAgent(ABC):
    """Abstract base class for review agents.

    All review agents must implement this interface. Agents analyze code
    in a workspace and return structured results with issues and scores.

    Implementing a new agent:
        1. Subclass BaseAgent
        2. Implement analyze() method
        3. Register with AgentRegistry
        4. Add to obra/agents/__init__.py

    Example:
        >>> class MyAgent(BaseAgent):
        ...     agent_type = AgentType.SECURITY
        ...
        ...     def analyze(self, item_id, changed_files, timeout_ms):
        ...         issues = self._check_for_issues(changed_files)
        ...         scores = self._calculate_scores(changed_files)
        ...         return AgentResult(
        ...             agent_type=self.agent_type,
        ...             status="complete",
        ...             issues=issues,
        ...             scores=scores
        ...         )
    """

    # Subclasses must set this
    agent_type: AgentType

    def __init__(self, working_dir: Path) -> None:
        """Initialize agent.

        Args:
            working_dir: Working directory containing code to analyze
        """
        self._working_dir = working_dir
        logger.debug(f"Initialized {self.__class__.__name__} for {working_dir}")

    @property
    def working_dir(self) -> Path:
        """Get working directory."""
        return self._working_dir

    @abstractmethod
    def analyze(
        self,
        item_id: str,
        changed_files: list[str] | None = None,
        timeout_ms: int = 60000,
    ) -> AgentResult:
        """Analyze code and return results.

        This is the main entry point for agent execution. Agents should
        analyze the code in working_dir and return issues and scores.

        Args:
            item_id: Plan item ID being reviewed
            changed_files: List of files that changed (optional, for focused review)
            timeout_ms: Maximum execution time in milliseconds

        Returns:
            AgentResult with issues and scores

        Raises:
            TimeoutError: If analysis exceeds timeout_ms
            Exception: If analysis fails
        """

    def get_files_to_analyze(
        self,
        changed_files: list[str] | None = None,
        extensions: list[str] | None = None,
    ) -> list[Path]:
        """Get list of files to analyze.

        Args:
            changed_files: If provided, only analyze these files
            extensions: If provided, filter by file extensions (e.g., [".py", ".js"])

        Returns:
            List of file paths to analyze
        """
        if changed_files:
            # Filter to existing files
            files = []
            for f in changed_files:
                path = self._working_dir / f if not Path(f).is_absolute() else Path(f)
                if path.exists() and path.is_file():
                    files.append(path)
            return files

        # Scan all files in working directory
        files = []
        ignore_dirs = {
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            ".tox",
            ".mypy_cache",
            ".pytest_cache",
            "dist",
            "build",
        }

        for path in self._working_dir.rglob("*"):
            # Skip ignored directories
            if any(part in ignore_dirs for part in path.parts):
                continue

            if not path.is_file():
                continue

            # Filter by extension if specified
            if extensions and path.suffix not in extensions:
                continue

            files.append(path)

        return files

    def read_file(self, path: Path) -> str:
        """Read file contents safely.

        Args:
            path: Path to file

        Returns:
            File contents or empty string if unreadable
        """
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not read {path}: {e}")
            return ""

    def _generate_issue_id(self, prefix: str, index: int) -> str:
        """Generate unique issue ID.

        Args:
            prefix: Agent prefix (e.g., "SEC", "TEST")
            index: Issue index

        Returns:
            Unique issue ID (e.g., "SEC-001")
        """
        return f"{prefix}-{index:03d}"

    def is_test_file(self, path: Path) -> bool:
        """Check if a file is a test file.

        Args:
            path: Path to check

        Returns:
            True if this is a test file
        """
        name = path.name
        # Standard pytest patterns
        if name.startswith("test_") or name.endswith("_test.py"):
            return True
        # Check if in a tests directory
        if "tests" in path.parts or "test" in path.parts:
            return True
        return False

    def is_excluded_file(self, path: Path) -> bool:
        """Check if a file should be excluded from analysis.

        Checks against common infrastructure files that shouldn't be
        analyzed as application code (conftest.py, setup.py, migrations, etc.)

        Args:
            path: Path to check

        Returns:
            True if file should be excluded
        """
        import fnmatch

        # Check exact filename matches
        if path.name in EXCLUDED_FILES:
            return True

        # Check patterns
        rel_path = str(path)
        for pattern in EXCLUDED_PATTERNS:
            if fnmatch.fnmatch(rel_path, pattern):
                return True

        return False


__all__ = ["AgentIssue", "AgentResult", "BaseAgent", "EXCLUDED_FILES", "EXCLUDED_PATTERNS"]
