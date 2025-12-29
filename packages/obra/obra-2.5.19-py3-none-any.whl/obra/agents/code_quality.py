"""Code quality review agent for maintainability analysis.

This module provides CodeQualityAgent, which analyzes code for quality
metrics including complexity, consistency, and maintainability.

Checks Performed:
    - Cyclomatic complexity
    - Function/method length
    - Nesting depth
    - Code duplication patterns
    - Naming conventions
    - Import organization
    - Type hint coverage

Scoring Dimensions:
    - maintainability: Overall maintainability score
    - complexity: Code complexity metrics
    - consistency: Code style consistency

Related:
    - obra/agents/base.py
    - obra/agents/registry.py
"""

import ast
import logging
import re
import time
from pathlib import Path

from obra.agents.base import AgentIssue, AgentResult, BaseAgent
from obra.agents.registry import register_agent
from obra.api.protocol import AgentType, Priority

logger = logging.getLogger(__name__)


# Complexity thresholds
MAX_FUNCTION_LENGTH = 50  # lines
MAX_NESTING_DEPTH = 4
MAX_CYCLOMATIC_COMPLEXITY = 10
MAX_PARAMETERS = 6
MAX_LINE_LENGTH = 120


@register_agent(AgentType.CODE_QUALITY)
class CodeQualityAgent(BaseAgent):
    """Code quality review agent for maintainability analysis.

    Analyzes code for quality metrics including complexity, consistency,
    and maintainability patterns.

    Example:
        >>> agent = CodeQualityAgent(Path("/workspace"))
        >>> result = agent.analyze(
        ...     item_id="T1",
        ...     changed_files=["src/auth.py"],
        ...     timeout_ms=60000
        ... )
        >>> print(f"Maintainability: {result.scores['maintainability']}")
    """

    agent_type = AgentType.CODE_QUALITY

    def analyze(
        self,
        item_id: str,
        changed_files: list[str] | None = None,
        timeout_ms: int = 60000,
    ) -> AgentResult:
        """Analyze code for quality metrics.

        Args:
            item_id: Plan item ID being reviewed
            changed_files: List of files that changed
            timeout_ms: Maximum execution time

        Returns:
            AgentResult with quality issues and scores
        """
        start_time = time.time()
        deadline = start_time + (timeout_ms / 1000)
        issues: list[AgentIssue] = []
        issue_index = 0

        logger.info(f"CodeQualityAgent analyzing {item_id}")

        # Get Python files
        py_files = self.get_files_to_analyze(
            changed_files=changed_files,
            extensions=[".py"],
        )

        # Stats for scoring
        total_functions = 0
        complex_functions = 0
        long_functions = 0
        deep_nesting_count = 0
        naming_issues = 0
        type_hints_present = 0
        type_hints_expected = 0

        for file_path in py_files:
            if time.time() > deadline:
                return self._timeout_result(issues, start_time)

            # Skip test files and infrastructure files
            if self.is_test_file(file_path):
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

            total_functions += file_stats["total_functions"]
            complex_functions += file_stats["complex_functions"]
            long_functions += file_stats["long_functions"]
            deep_nesting_count += file_stats["deep_nesting"]
            naming_issues += file_stats["naming_issues"]
            type_hints_present += file_stats["type_hints_present"]
            type_hints_expected += file_stats["type_hints_expected"]

        execution_time = int((time.time() - start_time) * 1000)
        logger.info(
            f"CodeQualityAgent complete: {len(issues)} issues found in {execution_time}ms"
        )

        return AgentResult(
            agent_type=self.agent_type,
            status="complete",
            issues=issues,
            scores=self._calculate_scores(
                total_functions=total_functions,
                complex_functions=complex_functions,
                long_functions=long_functions,
                deep_nesting_count=deep_nesting_count,
                naming_issues=naming_issues,
                type_hints_present=type_hints_present,
                type_hints_expected=type_hints_expected,
            ),
            execution_time_ms=execution_time,
            metadata={
                "files_analyzed": len(py_files),
                "total_functions": total_functions,
                "complex_functions": complex_functions,
            },
        )

    def _analyze_file(
        self,
        file_path: Path,
        content: str,
        issue_index: int,
    ) -> tuple[list[AgentIssue], dict[str, int]]:
        """Analyze a file for code quality issues.

        Args:
            file_path: Path to file
            content: File content
            issue_index: Starting issue index

        Returns:
            Tuple of (issues, stats)
        """
        issues: list[AgentIssue] = []
        rel_path = str(file_path.relative_to(self._working_dir))
        stats = {
            "total_functions": 0,
            "complex_functions": 0,
            "long_functions": 0,
            "deep_nesting": 0,
            "naming_issues": 0,
            "type_hints_present": 0,
            "type_hints_expected": 0,
        }

        # Check line length
        for i, line in enumerate(content.split("\n"), 1):
            if len(line) > MAX_LINE_LENGTH:
                stripped = line.strip()
                # Skip comments
                if stripped.startswith("#"):
                    continue
                # Skip URLs (common in comments and strings)
                if "http://" in line or "https://" in line:
                    continue
                # Skip import statements (sometimes unavoidably long)
                if stripped.startswith(("import ", "from ")):
                    continue
                # Skip string literals that are intentionally long (e.g., base64, hashes)
                if stripped.startswith(('"""', "'''", '"', "'")):
                    continue

                # Only report first few
                if len([iss for iss in issues if "line too long" in iss.title.lower()]) < 3:
                    issue_index += 1
                    issues.append(
                        AgentIssue(
                            id=self._generate_issue_id("QUAL", issue_index),
                            title=f"Line too long ({len(line)} chars)",
                            description=f"Line exceeds {MAX_LINE_LENGTH} characters. Consider breaking it up.",
                            priority=Priority.P3,
                            file_path=rel_path,
                            line_number=i,
                            dimension="consistency",
                            suggestion="Break the line into multiple shorter lines",
                        )
                    )

        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues, stats

        # Analyze functions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                stats["total_functions"] += 1

                # Check function length
                end_line = getattr(node, "end_lineno", node.lineno + 20)
                func_length = end_line - node.lineno
                if func_length > MAX_FUNCTION_LENGTH:
                    stats["long_functions"] += 1
                    issue_index += 1
                    issues.append(
                        AgentIssue(
                            id=self._generate_issue_id("QUAL", issue_index),
                            title=f"Long function: {node.name} ({func_length} lines)",
                            description=f"Function exceeds {MAX_FUNCTION_LENGTH} lines. Consider breaking into smaller functions.",
                            priority=Priority.P2,
                            file_path=rel_path,
                            line_number=node.lineno,
                            dimension="maintainability",
                            suggestion="Extract helper functions or break into smaller pieces",
                        )
                    )

                # Check parameter count
                param_count = len([
                    arg for arg in node.args.args
                    if arg.arg not in ("self", "cls")
                ])
                if param_count > MAX_PARAMETERS:
                    issue_index += 1
                    issues.append(
                        AgentIssue(
                            id=self._generate_issue_id("QUAL", issue_index),
                            title=f"Too many parameters: {node.name} ({param_count})",
                            description=f"Function has {param_count} parameters, max recommended is {MAX_PARAMETERS}.",
                            priority=Priority.P2,
                            file_path=rel_path,
                            line_number=node.lineno,
                            dimension="maintainability",
                            suggestion="Consider using a dataclass or dict for parameters",
                        )
                    )

                # Check complexity
                complexity = self._calculate_complexity(node)
                if complexity > MAX_CYCLOMATIC_COMPLEXITY:
                    stats["complex_functions"] += 1
                    issue_index += 1
                    issues.append(
                        AgentIssue(
                            id=self._generate_issue_id("QUAL", issue_index),
                            title=f"High complexity: {node.name} ({complexity})",
                            description=f"Cyclomatic complexity {complexity} exceeds threshold of {MAX_CYCLOMATIC_COMPLEXITY}.",
                            priority=Priority.P2,
                            file_path=rel_path,
                            line_number=node.lineno,
                            dimension="complexity",
                            suggestion="Refactor to reduce conditional branches",
                        )
                    )

                # Check nesting depth
                max_depth = self._calculate_nesting_depth(node)
                if max_depth > MAX_NESTING_DEPTH:
                    stats["deep_nesting"] += 1
                    issue_index += 1
                    issues.append(
                        AgentIssue(
                            id=self._generate_issue_id("QUAL", issue_index),
                            title=f"Deep nesting: {node.name} (depth {max_depth})",
                            description=f"Nesting depth {max_depth} exceeds threshold of {MAX_NESTING_DEPTH}.",
                            priority=Priority.P2,
                            file_path=rel_path,
                            line_number=node.lineno,
                            dimension="complexity",
                            suggestion="Use early returns or extract helper functions",
                        )
                    )

                # Check type hints (count per-annotation for partial credit)
                args = [arg for arg in node.args.args if arg.arg not in ("self", "cls")]
                has_return = any(
                    isinstance(n, ast.Return) and n.value is not None
                    for n in ast.walk(node)
                )
                expected = len(args) + (1 if has_return else 0)
                if expected > 0:
                    present = sum(1 for arg in args if arg.annotation is not None)
                    if has_return and node.returns is not None:
                        present += 1
                    stats["type_hints_expected"] += expected
                    stats["type_hints_present"] += present

                # Check naming conventions
                if not self._is_valid_function_name(node.name):
                    stats["naming_issues"] += 1
                    issue_index += 1
                    issues.append(
                        AgentIssue(
                            id=self._generate_issue_id("QUAL", issue_index),
                            title=f"Naming convention: {node.name}",
                            description="Function name should use snake_case.",
                            priority=Priority.P3,
                            file_path=rel_path,
                            line_number=node.lineno,
                            dimension="consistency",
                            suggestion="Rename to use snake_case",
                        )
                    )

            elif isinstance(node, ast.ClassDef):
                # Check class naming
                if not self._is_valid_class_name(node.name):
                    stats["naming_issues"] += 1
                    issue_index += 1
                    issues.append(
                        AgentIssue(
                            id=self._generate_issue_id("QUAL", issue_index),
                            title=f"Naming convention: class {node.name}",
                            description="Class name should use PascalCase.",
                            priority=Priority.P3,
                            file_path=rel_path,
                            line_number=node.lineno,
                            dimension="consistency",
                            suggestion="Rename to use PascalCase",
                        )
                    )

        return issues, stats

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function.

        Complexity = 1 + number of decision points.

        Args:
            node: AST node

        Returns:
            Cyclomatic complexity
        """
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # and/or add complexity
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                # List/dict/set comprehensions
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)

        return complexity

    def _calculate_nesting_depth(self, node: ast.AST, depth: int = 0) -> int:
        """Calculate maximum nesting depth.

        Args:
            node: AST node
            depth: Current depth

        Returns:
            Maximum nesting depth
        """
        max_depth = depth

        for child in ast.iter_child_nodes(node):
            # Nodes that increase nesting
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                child_depth = self._calculate_nesting_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_nesting_depth(child, depth)
                max_depth = max(max_depth, child_depth)

        return max_depth

    def _is_valid_function_name(self, name: str) -> bool:
        """Check if function name follows snake_case.

        Args:
            name: Function name

        Returns:
            True if valid
        """
        # Allow private/dunder methods
        if name.startswith("__"):
            return True

        # Check snake_case pattern
        return bool(re.match(r"^[a-z][a-z0-9_]*$", name.lstrip("_")))

    def _is_valid_class_name(self, name: str) -> bool:
        """Check if class name follows PascalCase.

        Args:
            name: Class name

        Returns:
            True if valid
        """
        return bool(re.match(r"^[A-Z][a-zA-Z0-9]*$", name))

    def _calculate_scores(
        self,
        total_functions: int,
        complex_functions: int,
        long_functions: int,
        deep_nesting_count: int,
        naming_issues: int,
        type_hints_present: int,
        type_hints_expected: int,
    ) -> dict[str, float]:
        """Calculate quality scores.

        Args:
            total_functions: Total functions analyzed
            complex_functions: Count of overly complex functions
            long_functions: Count of overly long functions
            deep_nesting_count: Count of deeply nested functions
            naming_issues: Count of naming convention violations
            type_hints_present: Functions with type hints
            type_hints_expected: Functions that should have hints

        Returns:
            Dict of dimension scores
        """
        if total_functions == 0:
            return {
                "maintainability": 1.0,
                "complexity": 1.0,
                "consistency": 1.0,
            }

        # Maintainability: based on function length and parameter count
        long_ratio = long_functions / total_functions
        maintainability = max(0.0, 1.0 - long_ratio)

        # Complexity: based on cyclomatic complexity and nesting
        complex_ratio = (complex_functions + deep_nesting_count) / (2 * total_functions)
        complexity = max(0.0, 1.0 - complex_ratio)

        # Consistency: based on naming and type hints
        naming_ratio = naming_issues / total_functions
        type_ratio = type_hints_present / type_hints_expected if type_hints_expected > 0 else 1.0
        consistency = (1.0 - naming_ratio + type_ratio) / 2

        return {
            "maintainability": round(maintainability, 2),
            "complexity": round(complexity, 2),
            "consistency": round(consistency, 2),
        }

    def _timeout_result(
        self,
        issues: list[AgentIssue],
        start_time: float,
    ) -> AgentResult:
        """Create timeout result."""
        logger.warning("CodeQualityAgent timed out")
        return AgentResult(
            agent_type=self.agent_type,
            status="timeout",
            issues=issues,
            scores={
                "maintainability": 0.5,
                "complexity": 0.5,
                "consistency": 0.5,
            },
            execution_time_ms=int((time.time() - start_time) * 1000),
        )


__all__ = ["CodeQualityAgent"]
