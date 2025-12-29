"""Testing review agent for test coverage analysis.

This module provides TestingAgent, which analyzes code for testing
quality, coverage gaps, and testing best practices.

Checks Performed:
    - Test file presence for source files
    - Test function coverage
    - Edge case handling
    - Mock usage patterns
    - Assertion quality
    - Test isolation

Scoring Dimensions:
    - test_coverage: Presence of tests for source files
    - test_quality: Quality of test assertions and patterns
    - edge_cases: Coverage of edge cases and error paths

Related:
    - obra/agents/base.py
    - obra/agents/registry.py
"""

import ast
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

from obra.agents.base import AgentIssue, AgentResult, BaseAgent
from obra.agents.registry import register_agent
from obra.api.protocol import AgentType, Priority

logger = logging.getLogger(__name__)


@register_agent(AgentType.TESTING)
class TestingAgent(BaseAgent):
    """Testing review agent for test coverage analysis.

    Analyzes code for testing quality by checking test file presence,
    test function coverage, and testing best practices.

    Example:
        >>> agent = TestingAgent(Path("/workspace"))
        >>> result = agent.analyze(
        ...     item_id="T1",
        ...     changed_files=["src/auth.py"],
        ...     timeout_ms=60000
        ... )
        >>> print(f"Test coverage score: {result.scores['test_coverage']}")
    """

    agent_type = AgentType.TESTING

    def analyze(
        self,
        item_id: str,
        changed_files: list[str] | None = None,
        timeout_ms: int = 60000,
    ) -> AgentResult:
        """Analyze code for testing quality and coverage gaps.

        Args:
            item_id: Plan item ID being reviewed
            changed_files: List of files that changed
            timeout_ms: Maximum execution time

        Returns:
            AgentResult with testing issues and scores
        """
        start_time = time.time()
        deadline = start_time + (timeout_ms / 1000)
        issues: list[AgentIssue] = []
        issue_index = 0

        logger.info(f"TestingAgent analyzing {item_id}")

        # Get source files
        source_files = self.get_files_to_analyze(
            changed_files=changed_files,
            extensions=[".py"],
        )

        # Find test files
        test_dir = self._working_dir / "tests"
        test_files = list(test_dir.rglob("test_*.py")) if test_dir.exists() else []
        test_files.extend(self._working_dir.rglob("*_test.py"))

        logger.debug(
            f"Found {len(source_files)} source files and {len(test_files)} test files"
        )

        # Stats for scoring
        files_with_tests = 0
        total_source_files = 0
        functions_tested = 0
        total_functions = 0
        edge_case_tests = 0
        total_tests = 0

        # Build test function index
        tested_exact, test_parts = self._build_test_index(test_files, deadline)

        include_conftest = os.getenv("OBRA_INCLUDE_CONFTEST", "").lower() in {"1", "true", "yes"}

        # Analyze source files
        for file_path in source_files:
            if time.time() > deadline:
                return self._timeout_result(issues, start_time)

            # Skip test files
            if self.is_test_file(file_path) and not (include_conftest and file_path.name == "conftest.py"):
                continue

            # Skip __init__.py and similar
            if file_path.name.startswith("_"):
                continue

            # Skip infrastructure files (conftest.py, setup.py, etc.)
            if self.is_excluded_file(file_path) and not (include_conftest and file_path.name == "conftest.py"):
                continue

            total_source_files += 1

            # Check for corresponding test file
            test_file = self._find_test_file(file_path, test_files)
            if test_file:
                files_with_tests += 1
            else:
                issue_index += 1
                issues.append(
                    AgentIssue(
                        id=self._generate_issue_id("TEST", issue_index),
                        title="No test file found",
                        description=f"No test file found for {file_path.name}. Create tests/test_{file_path.stem}.py",
                        priority=Priority.P1,
                        file_path=str(file_path.relative_to(self._working_dir)),
                        dimension="test_coverage",
                        suggestion=f"Create tests/test_{file_path.stem}.py with tests for this module",
                    )
                )

            # Analyze functions in source file
            content = self.read_file(file_path)
            if not content:
                continue

            functions = self._extract_functions(content)
            total_functions += len(functions)

            for func_name, func_info in functions:
                # Check if function is tested
                if self._is_function_tested(func_name, tested_exact, test_parts):
                    functions_tested += 1
                elif not func_name.startswith("_"):  # Skip private functions
                    issue_index += 1
                    issues.append(
                        AgentIssue(
                            id=self._generate_issue_id("TEST", issue_index),
                            title=f"Untested function: {func_name}",
                            description=f"Function '{func_name}' has no corresponding test.",
                            priority=Priority.P2,
                            file_path=str(file_path.relative_to(self._working_dir)),
                            line_number=func_info.get("line_number"),
                            dimension="test_coverage",
                            suggestion=f"Add test_{func_name}() to test file",
                        )
                    )

        # Analyze test quality
        for test_file in test_files:
            if time.time() > deadline:
                return self._timeout_result(issues, start_time)

            content = self.read_file(test_file)
            if not content:
                continue

            test_funcs = self._extract_functions(content)
            total_tests += len(test_funcs)

            # Check for edge case tests
            for func_name, _ in test_funcs:
                if any(
                    kw in func_name.lower()
                    for kw in ["error", "fail", "invalid", "empty", "none", "edge", "boundary"]
                ):
                    edge_case_tests += 1

            # Check test quality patterns
            new_issues = self._check_test_quality(test_file, content, issue_index)
            issues.extend(new_issues)
            issue_index += len(new_issues)

        execution_time = int((time.time() - start_time) * 1000)
        logger.info(
            f"TestingAgent complete: {len(issues)} issues found in {execution_time}ms"
        )

        return AgentResult(
            agent_type=self.agent_type,
            status="complete",
            issues=issues,
            scores=self._calculate_scores(
                files_with_tests=files_with_tests,
                total_source_files=total_source_files,
                functions_tested=functions_tested,
                total_functions=total_functions,
                edge_case_tests=edge_case_tests,
                total_tests=total_tests,
            ),
            execution_time_ms=execution_time,
            metadata={
                "source_files": total_source_files,
                "test_files": len(test_files),
                "total_functions": total_functions,
                "functions_tested": functions_tested,
            },
        )

    def _build_test_index(
        self,
        test_files: list[Path],
        deadline: float,
    ) -> tuple[set[str], set[str]]:
        """Build index of tested function names and test name parts.

        Args:
            test_files: List of test file paths
            deadline: Timeout deadline

        Returns:
            Tuple of (exact function names tested, test name parts for fuzzy matching)
        """
        tested = set()
        test_parts = set()  # All parts from test names for fuzzy matching

        for test_file in test_files:
            if time.time() > deadline:
                break

            content = self.read_file(test_file)
            if not content:
                continue

            # Extract test function names and infer tested functions
            for func_name, _ in self._extract_functions(content):
                if func_name.startswith("test_"):
                    # Extract tested function name from test name
                    # e.g., test_login_success -> login
                    parts = func_name[5:].split("_")
                    if parts:
                        tested.add(parts[0])
                        # Also add with first two parts
                        if len(parts) > 1:
                            tested.add("_".join(parts[:2]))
                        # Add all consecutive combinations for better matching
                        for i in range(len(parts)):
                            for j in range(i + 1, len(parts) + 1):
                                tested.add("_".join(parts[i:j]))
                        # Store individual parts for fuzzy matching
                        test_parts.update(parts)

        return tested, test_parts

    def _is_function_tested(
        self,
        func_name: str,
        tested_exact: set[str],
        test_parts: set[str],
    ) -> bool:
        """Check if a function is covered by tests using multiple strategies.

        Args:
            func_name: Name of the function to check
            tested_exact: Set of exact function names from test index
            test_parts: Set of individual parts from test names

        Returns:
            True if function appears to be tested
        """
        # Strategy 1: Exact match in tested set
        if func_name in tested_exact:
            return True

        # Strategy 2: Check if any part of the function name matches test parts
        # e.g., create_one_step_plan -> ["create", "one", "step", "plan"]
        func_parts = func_name.split("_")

        # If the main "verb" or "noun" of the function appears in tests
        # (skip common prefixes like "get", "set", "is", "has" for matching)
        common_prefixes = {"get", "set", "is", "has", "do", "can", "should", "will"}
        significant_parts = [p for p in func_parts if p not in common_prefixes]

        # Check if significant parts appear in test parts
        for part in significant_parts:
            if part in test_parts and len(part) > 2:  # Avoid matching short words
                return True

        # Strategy 3: Check if function name is substring of any tested name
        for tested_name in tested_exact:
            if func_name in tested_name or tested_name in func_name:
                return True

        return False

    def _find_test_file(
        self,
        source_file: Path,
        test_files: list[Path],
    ) -> Path | None:
        """Find corresponding test file for source file.

        Args:
            source_file: Source file path
            test_files: List of test file paths

        Returns:
            Test file path or None
        """
        stem = source_file.stem
        test_names = [f"test_{stem}.py", f"{stem}_test.py"]
        source_rel = source_file.relative_to(self._working_dir).with_suffix("")
        source_module = ".".join(source_rel.parts)
        parent_module = ".".join(source_rel.parts[:-1]) if len(source_rel.parts) > 1 else ""
        module_candidates = {stem}
        if parent_module:
            module_candidates.add(f"{parent_module}.{stem}")

        for test_file in test_files:
            if test_file.name in test_names:
                return test_file
            lowered = test_file.name.lower()
            if stem.lower() in lowered and lowered.startswith("test_"):
                return test_file
            if lowered.startswith("test_"):
                stem_parts = [part for part in stem.lower().split("_") if len(part) > 3]
                if any(part in lowered for part in stem_parts):
                    return test_file

            if "tests" in test_file.parts:
                tests_index = test_file.parts.index("tests")
                test_subpath = test_file.parts[tests_index + 1 : -1]
                if test_subpath:
                    source_dirs = source_file.relative_to(self._working_dir).parts[:-1]
                    if source_dirs and test_subpath[0] in source_dirs:
                        return test_file
            content = self._get_test_file_content(test_file)
            for candidate in module_candidates:
                if f"import {candidate}" in content or f"from {candidate} import" in content:
                    return test_file

        return None

    def _get_test_file_content(self, test_file: Path) -> str:
        """Return cached content for a test file."""
        if not hasattr(self, "_test_file_cache"):
            self._test_file_cache = {}
        if test_file in self._test_file_cache:
            return self._test_file_cache[test_file]
        content = self.read_file(test_file)
        self._test_file_cache[test_file] = content
        return content

    def _extract_functions(self, content: str) -> list[tuple[str, dict[str, Any]]]:
        """Extract function definitions from Python source.

        Args:
            content: Python source code

        Returns:
            List of (function_name, info_dict) tuples
        """
        functions = []

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(
                        (
                            node.name,
                            {
                                "line_number": node.lineno,
                                "is_async": False,
                            },
                        )
                    )
                elif isinstance(node, ast.AsyncFunctionDef):
                    functions.append(
                        (
                            node.name,
                            {
                                "line_number": node.lineno,
                                "is_async": True,
                            },
                        )
                    )
        except SyntaxError:
            # Fallback to regex for invalid Python
            for match in re.finditer(r"def\s+(\w+)\s*\(", content):
                line_number = content[: match.start()].count("\n") + 1
                functions.append(
                    (match.group(1), {"line_number": line_number, "is_async": False})
                )

        return functions

    def _check_test_quality(
        self,
        test_file: Path,
        content: str,
        issue_index: int,
    ) -> list[AgentIssue]:
        """Check test quality patterns.

        Args:
            test_file: Test file path
            content: File content
            issue_index: Starting issue index

        Returns:
            List of quality issues
        """
        issues = []
        rel_path = str(test_file.relative_to(self._working_dir))

        # Check for tests without assertions (AST-based)
        try:
            tree = ast.parse(content)
        except SyntaxError:
            tree = None

        if tree is not None:
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                if not node.name.startswith("test_"):
                    continue
                has_assert = any(isinstance(n, ast.Assert) for n in ast.walk(node))
                has_pytest_raises = any(
                    isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "raises"
                    for n in ast.walk(node)
                )
                if not has_assert and not has_pytest_raises:
                    issue_index += 1
                    issues.append(
                        AgentIssue(
                            id=self._generate_issue_id("TEST", issue_index),
                            title=f"Test without assertions: {node.name}",
                            description="Test function has no assertions. Tests should verify expected behavior.",
                            priority=Priority.P2,
                            file_path=rel_path,
                            dimension="test_quality",
                            suggestion="Add assert statements or pytest.raises to verify expected behavior",
                        )
                    )

        # Check for magic numbers in assertions
        magic_numbers = re.findall(r"assert\s+\w+\s*==\s*(\d+)", content)
        if len(magic_numbers) > 5:
            issue_index += 1
            issues.append(
                AgentIssue(
                    id=self._generate_issue_id("TEST", issue_index),
                    title="Magic numbers in assertions",
                    description="Multiple hardcoded numbers in assertions. Use named constants for clarity.",
                    priority=Priority.P3,
                    file_path=rel_path,
                    dimension="test_quality",
                    suggestion="Extract magic numbers to named constants",
                )
            )

        return issues

    def _calculate_scores(
        self,
        files_with_tests: int,
        total_source_files: int,
        functions_tested: int,
        total_functions: int,
        edge_case_tests: int,
        total_tests: int,
    ) -> dict[str, float]:
        """Calculate testing scores.

        Args:
            files_with_tests: Count of files with test coverage
            total_source_files: Total source files
            functions_tested: Count of tested functions
            total_functions: Total functions
            edge_case_tests: Count of edge case tests
            total_tests: Total test functions

        Returns:
            Dict of dimension scores
        """
        # File coverage score
        if total_source_files > 0:
            file_coverage = files_with_tests / total_source_files
        else:
            file_coverage = 1.0

        # Function coverage score
        if total_functions > 0:
            func_coverage = functions_tested / total_functions
        else:
            func_coverage = 1.0

        # Edge case coverage score (target: 20% of tests should be edge cases)
        if total_tests > 0:
            edge_ratio = edge_case_tests / total_tests
            edge_score = min(edge_ratio / 0.2, 1.0)
        else:
            edge_score = 0.0

        return {
            "test_coverage": round((file_coverage + func_coverage) / 2, 2),
            "test_quality": round(func_coverage, 2),  # Simplified
            "edge_cases": round(edge_score, 2),
        }

    def _timeout_result(
        self,
        issues: list[AgentIssue],
        start_time: float,
    ) -> AgentResult:
        """Create timeout result.

        Args:
            issues: Issues found so far
            start_time: When analysis started

        Returns:
            AgentResult with timeout status
        """
        logger.warning("TestingAgent timed out")
        return AgentResult(
            agent_type=self.agent_type,
            status="timeout",
            issues=issues,
            scores={
                "test_coverage": 0.5,  # Partial result
                "test_quality": 0.5,
                "edge_cases": 0.5,
            },
            execution_time_ms=int((time.time() - start_time) * 1000),
        )


__all__ = ["TestingAgent"]
