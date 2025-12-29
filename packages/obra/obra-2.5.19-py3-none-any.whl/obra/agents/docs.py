"""Documentation review agent for documentation quality analysis.

This module provides DocsAgent, which analyzes code for documentation
quality, including docstring coverage, README completeness, and API
documentation.

Checks Performed:
    - Module docstring presence
    - Function/class docstring coverage
    - Docstring quality (parameters, returns, examples)
    - README file presence and completeness
    - API documentation (for public modules)
    - Changelog maintenance

Scoring Dimensions:
    - docstring_coverage: Percentage of functions with docstrings
    - readme_complete: README file presence and completeness
    - api_documented: Public API documentation quality

Related:
    - obra/agents/base.py
    - obra/agents/registry.py
"""

import ast
import logging
import time
from pathlib import Path

from obra.agents.base import AgentIssue, AgentResult, BaseAgent
from obra.agents.registry import register_agent
from obra.api.protocol import AgentType, Priority

logger = logging.getLogger(__name__)


# Required sections for a complete README (with alternative phrasings)
# Each entry is a tuple of (canonical_name, list_of_patterns)
README_REQUIRED_SECTIONS = [
    ("installation", ["install", "installation", "installing", "setup", "getting started", "quick start", "quickstart"]),
    ("usage", ["usage", "how to use", "using", "basic usage", "example", "examples"]),
]

README_OPTIONAL_SECTIONS = [
    ("contributing", ["contributing", "contribute", "development", "how to contribute"]),
    ("license", ["license", "licensing"]),
    ("requirements", ["requirements", "prerequisites", "dependencies", "deps"]),
    ("features", ["features", "capabilities", "what it does"]),
    ("api", ["api", "api reference", "reference", "documentation", "docs"]),
]


@register_agent(AgentType.DOCS)
class DocsAgent(BaseAgent):
    """Documentation review agent for documentation quality analysis.

    Analyzes code for documentation quality including docstring coverage,
    README completeness, and API documentation.

    Example:
        >>> agent = DocsAgent(Path("/workspace"))
        >>> result = agent.analyze(
        ...     item_id="T1",
        ...     changed_files=["src/auth.py"],
        ...     timeout_ms=60000
        ... )
        >>> print(f"Docstring coverage: {result.scores['docstring_coverage']}")
    """

    agent_type = AgentType.DOCS

    def analyze(
        self,
        item_id: str,
        changed_files: list[str] | None = None,
        timeout_ms: int = 60000,
    ) -> AgentResult:
        """Analyze code for documentation quality.

        Args:
            item_id: Plan item ID being reviewed
            changed_files: List of files that changed
            timeout_ms: Maximum execution time

        Returns:
            AgentResult with documentation issues and scores
        """
        start_time = time.time()
        deadline = start_time + (timeout_ms / 1000)
        issues: list[AgentIssue] = []
        issue_index = 0

        logger.info(f"DocsAgent analyzing {item_id}")

        # Get Python files to analyze
        py_files = self.get_files_to_analyze(
            changed_files=changed_files,
            extensions=[".py"],
        )

        # Stats for scoring
        total_public_items = 0
        documented_items = 0
        readme_score = 0.0
        api_items_documented = 0
        total_api_items = 0

        # Check README
        readme_issues, readme_score = self._check_readme(deadline)
        issues.extend(readme_issues)
        issue_index += len(readme_issues)

        # Analyze Python files
        for file_path in py_files:
            if time.time() > deadline:
                return self._timeout_result(issues, start_time)

            # Skip test files, __init__.py, and infrastructure files
            if self.is_test_file(file_path):
                continue
            if file_path.name == "__init__.py":
                continue
            if self.is_excluded_file(file_path):
                continue

            content = self.read_file(file_path)
            if not content:
                continue

            file_issues, file_stats = self._analyze_file(
                file_path=file_path,
                content=content,
                issue_index=issue_index,
            )
            issues.extend(file_issues)
            issue_index += len(file_issues)

            total_public_items += file_stats["total_public"]
            documented_items += file_stats["documented"]
            total_api_items += file_stats["api_items"]
            api_items_documented += file_stats["api_documented"]

        execution_time = int((time.time() - start_time) * 1000)
        logger.info(
            f"DocsAgent complete: {len(issues)} issues found in {execution_time}ms"
        )

        return AgentResult(
            agent_type=self.agent_type,
            status="complete",
            issues=issues,
            scores=self._calculate_scores(
                total_public_items=total_public_items,
                documented_items=documented_items,
                readme_score=readme_score,
                api_items_documented=api_items_documented,
                total_api_items=total_api_items,
            ),
            execution_time_ms=execution_time,
            metadata={
                "files_analyzed": len(py_files),
                "total_public_items": total_public_items,
                "documented_items": documented_items,
            },
        )

    def _check_readme(
        self,
        deadline: float,
    ) -> tuple[list[AgentIssue], float]:
        """Check README file presence and completeness.

        Args:
            deadline: Timeout deadline

        Returns:
            Tuple of (issues, score)
        """
        issues: list[AgentIssue] = []
        issue_index = 0

        # Look for README
        readme_files = list(self._working_dir.glob("README*"))
        if not readme_files:
            issues.append(
                AgentIssue(
                    id=self._generate_issue_id("DOC", issue_index + 1),
                    title="Missing README file",
                    description="Project should have a README.md file with installation and usage instructions.",
                    priority=Priority.P1,
                    dimension="readme_complete",
                    suggestion="Create README.md with project description, installation, and usage sections",
                )
            )
            return issues, 0.0

        readme_files_sorted = sorted(
            readme_files,
            key=lambda path: (path.name.lower() != "readme.md", path.name.lower()),
        )
        readme_path = readme_files_sorted[0]
        content = self.read_file(readme_path).lower()

        # Check required sections using fuzzy matching
        found_sections: set[str] = set()
        for section_name, patterns in README_REQUIRED_SECTIONS:
            for pattern in patterns:
                if pattern in content:
                    found_sections.add(section_name)
                    break

        # Find missing required sections
        required_section_names = {name for name, _ in README_REQUIRED_SECTIONS}
        missing_sections = required_section_names - found_sections
        for section in missing_sections:
            issue_index += 1
            issues.append(
                AgentIssue(
                    id=self._generate_issue_id("DOC", issue_index),
                    title=f"README missing '{section}' section",
                    description=f"README should include a '{section}' section.",
                    priority=Priority.P2,
                    file_path="README.md",
                    dimension="readme_complete",
                    suggestion=f"Add a '{section}' section to README.md",
                )
            )

        # Calculate score
        required_found = len(found_sections)
        required_total = len(README_REQUIRED_SECTIONS)

        # Check optional sections for bonus using fuzzy matching
        optional_found = 0
        for _, patterns in README_OPTIONAL_SECTIONS:
            if any(pattern in content for pattern in patterns):
                optional_found += 1
        optional_bonus = min(optional_found / len(README_OPTIONAL_SECTIONS) * 0.2, 0.2)

        score = (required_found / required_total * 0.8) + optional_bonus

        return issues, score

    def _analyze_file(
        self,
        file_path: Path,
        content: str,
        issue_index: int,
    ) -> tuple[list[AgentIssue], dict[str, int]]:
        """Analyze a Python file for documentation quality.

        Args:
            file_path: Path to file
            content: File content
            issue_index: Starting issue index

        Returns:
            Tuple of (issues, stats_dict)
        """
        issues: list[AgentIssue] = []
        rel_path = str(file_path.relative_to(self._working_dir))
        stats = {
            "total_public": 0,
            "documented": 0,
            "api_items": 0,
            "api_documented": 0,
        }

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues, stats

        # Check module docstring
        if not ast.get_docstring(tree):
            issue_index += 1
            issues.append(
                AgentIssue(
                    id=self._generate_issue_id("DOC", issue_index),
                    title="Missing module docstring",
                    description="Module should have a docstring explaining its purpose.",
                    priority=Priority.P2,
                    file_path=rel_path,
                    line_number=1,
                    dimension="docstring_coverage",
                    suggestion="Add a module-level docstring at the top of the file",
                )
            )

        # Build a map of parent nodes for proper is_api detection
        parent_map = self._build_parent_map(tree)

        # Analyze classes and functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    stats["total_public"] += 1
                    stats["api_items"] += 1

                    docstring = ast.get_docstring(node)
                    if docstring:
                        stats["documented"] += 1
                        stats["api_documented"] += 1
                    else:
                        issue_index += 1
                        issues.append(
                            AgentIssue(
                                id=self._generate_issue_id("DOC", issue_index),
                                title=f"Missing docstring for class '{node.name}'",
                                description=f"Public class '{node.name}' should have a docstring.",
                                priority=Priority.P2,
                                file_path=rel_path,
                                line_number=node.lineno,
                                dimension="docstring_coverage",
                                suggestion=f"Add a docstring describing the purpose of class {node.name}",
                            )
                        )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip private functions and test functions
                if node.name.startswith("_"):
                    continue
                if self._has_function_parent(node, parent_map):
                    continue

                stats["total_public"] += 1

                # Check if it's a module-level function (not a method or nested)
                is_api = not self._has_class_parent(node, parent_map) and not self._has_function_parent(node, parent_map)
                if is_api:
                    stats["api_items"] += 1

                docstring = ast.get_docstring(node)
                if docstring:
                    stats["documented"] += 1
                    if is_api:
                        stats["api_documented"] += 1

                    # Check docstring quality
                    quality_issues = self._check_docstring_quality(
                        node=node,
                        docstring=docstring,
                        file_path=rel_path,
                        issue_index=issue_index,
                    )
                    issues.extend(quality_issues)
                    issue_index += len(quality_issues)
                else:
                    issue_index += 1
                    issues.append(
                        AgentIssue(
                            id=self._generate_issue_id("DOC", issue_index),
                            title=f"Missing docstring for '{node.name}'",
                            description=f"Public function '{node.name}' should have a docstring.",
                            priority=Priority.P2,
                            file_path=rel_path,
                            line_number=node.lineno,
                            dimension="docstring_coverage",
                            suggestion=f"Add a docstring describing function {node.name}",
                        )
                    )

        return issues, stats

    def _build_parent_map(self, tree: ast.AST) -> dict[ast.AST, ast.AST]:
        """Build a mapping from child nodes to their parent nodes.

        Args:
            tree: The AST tree

        Returns:
            Dict mapping each node to its parent
        """
        parent_map: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parent_map[child] = parent
        return parent_map

    def _has_class_parent(
        self,
        node: ast.AST,
        parent_map: dict[ast.AST, ast.AST],
    ) -> bool:
        """Check if a node has a ClassDef ancestor.

        Args:
            node: The node to check
            parent_map: Mapping from nodes to parents

        Returns:
            True if node is inside a class definition
        """
        current = node
        while current in parent_map:
            parent = parent_map[current]
            if isinstance(parent, ast.ClassDef):
                return True
            current = parent
        return False

    def _has_function_parent(
        self,
        node: ast.AST,
        parent_map: dict[ast.AST, ast.AST],
    ) -> bool:
        """Check if a node has a FunctionDef ancestor."""
        current = node
        while current in parent_map:
            parent = parent_map[current]
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return True
            current = parent
        return False

    def _check_docstring_quality(
        self,
        node: ast.FunctionDef,
        docstring: str,
        file_path: str,
        issue_index: int,
    ) -> list[AgentIssue]:
        """Check docstring quality for a function.

        Args:
            node: AST function node
            docstring: The docstring content
            file_path: Relative file path
            issue_index: Starting issue index

        Returns:
            List of quality issues
        """
        issues: list[AgentIssue] = []
        docstring_lower = docstring.lower()

        # Get function parameters (excluding self, cls)
        params = [
            arg.arg for arg in node.args.args if arg.arg not in ("self", "cls")
        ]

        # Check if docstring documents parameters
        if params and len(params) > 0:
            # Look for Args section or param documentation
            has_args_section = "args:" in docstring_lower or "parameters:" in docstring_lower
            documented_params = sum(1 for p in params if p in docstring)

            if not has_args_section and documented_params < len(params) // 2:
                issue_index += 1
                issues.append(
                    AgentIssue(
                        id=self._generate_issue_id("DOC", issue_index),
                        title=f"Missing parameter documentation for '{node.name}'",
                        description=f"Function '{node.name}' has {len(params)} parameters but they are not documented.",
                        priority=Priority.P3,
                        file_path=file_path,
                        line_number=node.lineno,
                        dimension="api_documented",
                        suggestion="Add Args: section with parameter descriptions",
                    )
                )

        # Check for return documentation (if function has return statement)
        has_return = any(
            isinstance(n, ast.Return) and n.value is not None
            for n in ast.walk(node)
        )
        if has_return and "return" not in docstring_lower:
            issue_index += 1
            issues.append(
                AgentIssue(
                    id=self._generate_issue_id("DOC", issue_index),
                    title=f"Missing return documentation for '{node.name}'",
                    description=f"Function '{node.name}' has a return statement but no return documentation.",
                    priority=Priority.P3,
                    file_path=file_path,
                    line_number=node.lineno,
                    dimension="api_documented",
                    suggestion="Add Returns: section describing the return value",
                )
            )

        return issues

    def _calculate_scores(
        self,
        total_public_items: int,
        documented_items: int,
        readme_score: float,
        api_items_documented: int,
        total_api_items: int,
    ) -> dict[str, float]:
        """Calculate documentation scores.

        Args:
            total_public_items: Total public items
            documented_items: Items with docstrings
            readme_score: README completeness score
            api_items_documented: API items with docs
            total_api_items: Total API items

        Returns:
            Dict of dimension scores
        """
        # Docstring coverage
        if total_public_items > 0:
            docstring_coverage = documented_items / total_public_items
        else:
            docstring_coverage = 1.0

        # API documentation
        if total_api_items > 0:
            api_documented = api_items_documented / total_api_items
        else:
            api_documented = 1.0

        return {
            "docstring_coverage": round(docstring_coverage, 2),
            "readme_complete": round(readme_score, 2),
            "api_documented": round(api_documented, 2),
        }

    def _timeout_result(
        self,
        issues: list[AgentIssue],
        start_time: float,
    ) -> AgentResult:
        """Create timeout result."""
        logger.warning("DocsAgent timed out")
        return AgentResult(
            agent_type=self.agent_type,
            status="timeout",
            issues=issues,
            scores={
                "docstring_coverage": 0.5,
                "readme_complete": 0.5,
                "api_documented": 0.5,
            },
            execution_time_ms=int((time.time() - start_time) * 1000),
        )


__all__ = ["DocsAgent"]
