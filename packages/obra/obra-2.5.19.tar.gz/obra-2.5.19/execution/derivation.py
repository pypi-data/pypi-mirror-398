"""Derivation engine for breaking down objectives into implementation plans.

This module provides the DerivationEngine class that uses LLM invocation
to transform high-level objectives into structured implementation plans.

The engine:
    1. Gathers project context (files, structure, README)
    2. Builds a derivation prompt with context and constraints
    3. Invokes LLM with optional extended thinking
    4. Parses structured output into plan items

Related:
    - docs/design/prds/UNIFIED_HYBRID_ARCHITECTURE_PRD.md Section 1
    - obra/hybrid/handlers/derive.py (handler layer)
    - obra/llm/invoker.py (LLM invocation)
    - src/derivation/engine.py (CLI implementation reference)
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from obra.llm.invoker import LLMInvoker

logger = logging.getLogger(__name__)


# Work type detection patterns (aligned with CLI src/derivation/engine.py)
WORK_TYPE_KEYWORDS: dict[str, list[str]] = {
    "feature_implementation": ["implement", "create", "build", "add feature", "new feature"],
    "bug_fix": ["fix", "bug", "issue", "error", "broken", "failing"],
    "refactoring": ["refactor", "restructure", "reorganize", "clean up", "simplify"],
    "integration": ["integrate", "connect", "api", "external", "third-party"],
    "database": ["database", "schema", "migration", "table", "column", "index"],
}

# Work phases (4-phase workflow)
VALID_PHASES = ["explore", "plan", "implement", "commit"]

# Work types that benefit from exploration phase
WORK_TYPES_NEEDING_EXPLORATION = ["feature_implementation", "refactoring", "integration"]


@dataclass
class DerivationResult:
    """Result from plan derivation.

    Attributes:
        plan_items: List of derived plan items
        raw_response: Raw LLM response for debugging
        work_type: Detected work type
        duration_seconds: Time taken for derivation
        tokens_used: Estimated tokens used
        success: Whether derivation succeeded
        error_message: Error message if failed
    """

    plan_items: list[dict[str, Any]] = field(default_factory=list)
    raw_response: str = ""
    work_type: str = "general"
    duration_seconds: float = 0.0
    tokens_used: int = 0
    success: bool = True
    error_message: str = ""

    @property
    def item_count(self) -> int:
        """Number of derived plan items."""
        return len(self.plan_items)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "plan_items": self.plan_items,
            "raw_response": self.raw_response,
            "work_type": self.work_type,
            "duration_seconds": self.duration_seconds,
            "tokens_used": self.tokens_used,
            "success": self.success,
            "error_message": self.error_message,
            "item_count": self.item_count,
        }


class DerivationEngine:
    """Engine for deriving implementation plans from objectives.

    Uses LLM invocation to break down high-level objectives into
    structured plan items (tasks/stories) with proper sequencing
    and dependencies.

    Example:
        >>> from obra.llm.invoker import LLMInvoker
        >>> invoker = LLMInvoker()
        >>> engine = DerivationEngine(
        ...     working_dir=Path("/path/to/project"),
        ...     llm_invoker=invoker,
        ... )
        >>> result = engine.derive("Add user authentication")
        >>> for item in result.plan_items:
        ...     print(f"{item['id']}: {item['title']}")

    Thread-safety:
        Thread-safe through LLMInvoker's thread safety guarantees.

    Related:
        - obra/hybrid/handlers/derive.py (handler layer)
        - obra/llm/invoker.py (LLM invocation)
    """

    def __init__(
        self,
        working_dir: Path,
        llm_invoker: Optional["LLMInvoker"] = None,
        thinking_enabled: bool = True,
        thinking_level: str = "high",
        max_items: int = 20,
    ) -> None:
        """Initialize DerivationEngine.

        Args:
            working_dir: Working directory for file access
            llm_invoker: LLMInvoker instance for LLM calls
            thinking_enabled: Whether to use extended thinking
            thinking_level: Thinking level (off, minimal, standard, high, maximum)
            max_items: Maximum plan items to generate
        """
        self._working_dir = working_dir
        self._llm_invoker = llm_invoker
        self._thinking_enabled = thinking_enabled
        self._thinking_level = thinking_level
        self._max_items = max_items

        logger.debug(
            f"DerivationEngine initialized: working_dir={working_dir}, "
            f"thinking_enabled={thinking_enabled}, thinking_level={thinking_level}"
        )

    def derive(
        self,
        objective: str,
        project_context: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
        provider: str = "anthropic",
    ) -> DerivationResult:
        """Derive implementation plan from objective.

        Args:
            objective: Task objective to plan for
            project_context: Optional project context (languages, frameworks)
            constraints: Optional derivation constraints
            provider: LLM provider to use

        Returns:
            DerivationResult with plan items and metadata

        Example:
            >>> result = engine.derive(
            ...     "Add user authentication",
            ...     project_context={"languages": ["python"]},
            ...     constraints={"max_items": 10},
            ... )
        """
        start_time = time.time()

        try:
            # Detect work type
            work_type = self._detect_work_type(objective)

            # Gather local context
            context = self._gather_context(project_context or {})

            # Build prompt
            prompt = self._build_prompt(
                objective=objective,
                context=context,
                constraints=constraints or {},
                work_type=work_type,
            )

            # Invoke LLM
            raw_response, tokens_used = self._invoke_llm(
                prompt=prompt,
                provider=provider,
                work_type=work_type,
            )

            # Parse response
            plan_items = self._parse_response(raw_response)

            duration = time.time() - start_time
            logger.info(
                f"Derivation completed: {len(plan_items)} items, "
                f"{duration:.2f}s, work_type={work_type}"
            )

            return DerivationResult(
                plan_items=plan_items,
                raw_response=raw_response,
                work_type=work_type,
                duration_seconds=duration,
                tokens_used=tokens_used,
                success=True,
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Derivation failed: {e}")
            return DerivationResult(
                success=False,
                error_message=str(e),
                duration_seconds=duration,
            )

    def _detect_work_type(self, objective: str) -> str:
        """Detect work type from objective text.

        Args:
            objective: Task objective

        Returns:
            Work type string
        """
        text = objective.lower()

        for work_type, keywords in WORK_TYPE_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                logger.debug(f"Detected work type: {work_type}")
                return work_type

        return "general"

    def _gather_context(self, project_context: dict[str, Any]) -> dict[str, Any]:
        """Gather local context for derivation.

        Args:
            project_context: Base project context

        Returns:
            Enhanced context dictionary
        """
        context = dict(project_context)

        # Add file structure summary
        try:
            structure = self._summarize_structure()
            context["file_structure"] = structure
        except Exception as e:
            logger.warning(f"Failed to gather file structure: {e}")

        # Add README if exists
        readme_path = self._working_dir / "README.md"
        if readme_path.exists():
            try:
                content = readme_path.read_text(encoding="utf-8")
                # Truncate to first 2000 chars
                context["readme"] = content[:2000] + ("..." if len(content) > 2000 else "")
            except Exception:
                pass

        return context

    def _summarize_structure(self) -> list[str]:
        """Summarize project file structure.

        Returns:
            List of important file paths
        """
        important_files: list[str] = []
        important_patterns = [
            "*.py",
            "*.js",
            "*.ts",
            "*.tsx",
            "*.jsx",
            "package.json",
            "pyproject.toml",
            "requirements.txt",
            "Cargo.toml",
            "go.mod",
            "README.md",
            "Makefile",
            "Dockerfile",
        ]

        max_files = 50
        skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

        for pattern in important_patterns:
            for path in self._working_dir.rglob(pattern):
                if any(skip_dir in path.parts for skip_dir in skip_dirs):
                    continue

                try:
                    rel_path = path.relative_to(self._working_dir)
                    important_files.append(str(rel_path))
                except ValueError:
                    continue

                if len(important_files) >= max_files:
                    break

            if len(important_files) >= max_files:
                break

        return sorted(important_files)[:max_files]

    def _build_prompt(
        self,
        objective: str,
        context: dict[str, Any],
        constraints: dict[str, Any],
        work_type: str,
    ) -> str:
        """Build derivation prompt.

        Args:
            objective: Task objective
            context: Project context
            constraints: Derivation constraints
            work_type: Detected work type

        Returns:
            Prompt string for LLM
        """
        # Build context section
        context_parts = []

        if context.get("languages"):
            context_parts.append(f"Languages: {', '.join(context['languages'])}")

        if context.get("frameworks"):
            context_parts.append(f"Frameworks: {', '.join(context['frameworks'])}")

        if context.get("file_structure"):
            files = context["file_structure"][:20]
            context_parts.append(f"Key files: {', '.join(files)}")

        if context.get("readme"):
            context_parts.append(f"README excerpt:\n{context['readme'][:500]}")

        context_section = "\n".join(context_parts) if context_parts else "No project context available."

        # Build constraints section
        max_items = constraints.get("max_items", self._max_items)
        constraints_section = f"- Maximum {max_items} plan items\n"

        if constraints.get("scope_boundaries"):
            constraints_section += f"- Scope boundaries: {', '.join(constraints['scope_boundaries'])}\n"

        # Get pattern guidance
        pattern_guidance = self._get_pattern_guidance(work_type)

        # 4-phase guidance for complex work types
        four_phase_guidance = ""
        if work_type in WORK_TYPES_NEEDING_EXPLORATION:
            four_phase_guidance = """
## Recommended Phase Structure (4-Phase Workflow)

For best results, structure derived items to follow the 4-phase workflow:

1. **Explore** (work_phase: "explore")
   - Research existing code, patterns, dependencies
   - Do NOT write implementation code in this phase

2. **Plan** (work_phase: "plan")
   - Design the approach based on exploration
   - Create implementation plan

3. **Implement** (work_phase: "implement")
   - Execute the plan step by step
   - Reference the plan to stay on track

4. **Commit** (work_phase: "commit")
   - Run tests, verify, commit
   - Update documentation

Not all work requires all phases. Bug fixes may skip exploration.
Simple tasks may skip planning. Use judgment based on complexity.
"""

        prompt = f"""You are an expert software architect. Derive an implementation plan for the following objective.

## Objective
{objective}

## Project Context
{context_section}

## Work Type Detected: {work_type}
{pattern_guidance}

## Constraints
{constraints_section}
{four_phase_guidance}
## Instructions
Create a structured implementation plan with the following requirements:
1. Break the objective into logical tasks/stories
2. Each item should be independently testable
3. Order items by dependencies (items that must be done first come first)
4. Be specific about what each item accomplishes
5. Include acceptance criteria for each item
6. Classify each item's work_phase if applicable (explore, plan, implement, commit)

## Output Format
Return a JSON object with a "plan_items" array. Each item should have:
- id: Unique identifier (e.g., "T1", "T2")
- item_type: "task" or "story"
- title: Brief title
- description: Detailed description
- acceptance_criteria: Array of criteria strings
- dependencies: Array of item IDs this depends on
- work_phase: "explore" | "plan" | "implement" | "commit" (optional)

Example:
```json
{{
  "plan_items": [
    {{
      "id": "T1",
      "item_type": "task",
      "title": "Research existing authentication patterns",
      "description": "Explore the codebase to understand existing auth patterns",
      "acceptance_criteria": ["Auth patterns documented", "Dependencies identified"],
      "dependencies": [],
      "work_phase": "explore"
    }},
    {{
      "id": "T2",
      "item_type": "task",
      "title": "Implement login endpoint",
      "description": "Create POST /login endpoint that validates credentials",
      "acceptance_criteria": ["Endpoint returns JWT on valid credentials", "Returns 401 on invalid"],
      "dependencies": ["T1"],
      "work_phase": "implement"
    }}
  ]
}}
```

Return ONLY the JSON object, no additional text.
"""
        return prompt

    def _get_pattern_guidance(self, work_type: str) -> str:
        """Get decomposition guidance for work type.

        Args:
            work_type: Detected work type

        Returns:
            Pattern guidance string
        """
        patterns = {
            "feature_implementation": """
Recommended decomposition pattern for feature implementation:
1. Design data models and API interfaces (explore/plan phase)
2. Implement core functionality (implement phase)
3. Add comprehensive test coverage (implement phase)
4. Write user documentation and examples (commit phase)""",
            "bug_fix": """
Recommended decomposition pattern for bug fix:
1. Reproduce the bug with minimal test case (explore phase)
2. Identify root cause and implement fix (implement phase)
3. Add regression tests to prevent recurrence (implement phase)
4. Verify fix in production-like environment (commit phase)""",
            "refactoring": """
Recommended decomposition pattern for refactoring:
1. Analyze current code structure and identify issues (explore phase)
2. Plan refactoring approach and migration strategy (plan phase)
3. Execute refactoring with test coverage maintained (implement phase)
4. Validate functionality and performance (commit phase)""",
            "integration": """
Recommended decomposition pattern for integration:
1. Design integration interfaces and contracts (explore/plan phase)
2. Implement integration layer with error handling (implement phase)
3. Add integration tests and mocking (implement phase)
4. Document integration setup and usage (commit phase)""",
            "database": """
Recommended decomposition pattern for database changes:
1. Design schema changes and migration strategy (plan phase)
2. Implement migration scripts with rollback (implement phase)
3. Update ORM models and queries (implement phase)
4. Test migration on staging environment (commit phase)""",
            "general": """
Recommended decomposition pattern:
1. Research and understand requirements (explore phase)
2. Design solution approach (plan phase)
3. Implement core changes with tests (implement phase)
4. Validate and document changes (commit phase)""",
        }

        return patterns.get(work_type, patterns["general"])

    def _invoke_llm(
        self,
        prompt: str,
        provider: str,
        work_type: str,
    ) -> tuple[str, int]:
        """Invoke LLM to generate plan.

        Args:
            prompt: Derivation prompt
            provider: LLM provider name
            work_type: Detected work type

        Returns:
            Tuple of (raw_response, tokens_used)
        """
        if self._llm_invoker is None:
            logger.warning("No LLM invoker configured, returning placeholder")
            return self._placeholder_response(), 0

        # Determine thinking level
        thinking_level = None
        if self._thinking_enabled:
            thinking_level = self._thinking_level

        # Invoke LLM
        result = self._llm_invoker.invoke(
            prompt=prompt,
            provider=provider,
            thinking_level=thinking_level,
            response_format="json",
        )

        return result.content, result.tokens_used

    def _placeholder_response(self) -> str:
        """Generate placeholder response when no LLM available.

        Returns:
            Placeholder JSON response
        """
        return json.dumps({
            "plan_items": [
                {
                    "id": "T1",
                    "item_type": "task",
                    "title": "Placeholder task",
                    "description": "LLM invoker not configured - configure via obra/llm/invoker.py",
                    "acceptance_criteria": ["LLM invocation implemented"],
                    "dependencies": [],
                    "work_phase": "implement",
                }
            ]
        })

    def _parse_response(self, raw_response: str) -> list[dict[str, Any]]:
        """Parse LLM response into plan items.

        Args:
            raw_response: Raw LLM response

        Returns:
            List of plan item dictionaries
        """
        try:
            response = raw_response.strip()

            # Check for empty response
            if not response:
                logger.error("Received empty response from LLM")
                return self._create_diagnostic_fallback(
                    "Empty response",
                    "LLM returned empty content. Check LLM provider configuration and API key.",
                    raw_response
                )

            # Handle markdown code blocks
            if response.startswith("```"):
                lines = response.split("\n")
                start = 1 if lines[0].startswith("```") else 0
                end = len(lines) - 1 if lines[-1] == "```" else len(lines)
                response = "\n".join(lines[start:end])

            # Parse JSON
            data = json.loads(response)

            # Extract plan_items
            if isinstance(data, dict) and "plan_items" in data:
                items = data["plan_items"]
            elif isinstance(data, list):
                items = data
            else:
                logger.warning("Unexpected response format")
                items = [data]

            # Validate and normalize items
            normalized = []
            for i, item in enumerate(items):
                # Validate work_phase
                work_phase = item.get("work_phase", "implement")
                if work_phase not in VALID_PHASES:
                    work_phase = "implement"

                normalized_item = {
                    "id": item.get("id", f"T{i + 1}"),
                    "item_type": item.get("item_type", "task"),
                    "title": item.get("title", "Untitled"),
                    "description": item.get("description", ""),
                    "acceptance_criteria": item.get("acceptance_criteria", []),
                    "dependencies": item.get("dependencies", []),
                    "work_phase": work_phase,
                }
                normalized.append(normalized_item)

            # Enforce max items
            if len(normalized) > self._max_items:
                logger.warning(
                    f"Truncating {len(normalized)} items to max {self._max_items}"
                )
                normalized = normalized[:self._max_items]

            return normalized

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan JSON: {e}")
            logger.error(f"Raw response (first 500 chars): {raw_response[:500]}")
            return self._create_diagnostic_fallback(
                f"JSON parse error: {e!s}",
                self._generate_parse_error_diagnostic(e, raw_response),
                raw_response
            )

    def _create_diagnostic_fallback(
        self, error_type: str, diagnostic: str, raw_response: str
    ) -> list[dict[str, Any]]:
        """Create diagnostic fallback task with detailed information.

        Args:
            error_type: Type of error encountered
            diagnostic: Detailed diagnostic message
            raw_response: Raw LLM response for reference

        Returns:
            List containing single diagnostic task
        """
        # Truncate raw response for description (keep it manageable)
        response_preview = raw_response[:200] if raw_response else "(empty)"
        if len(raw_response) > 200:
            response_preview += "... (truncated)"

        # Save full response to a debug file for investigation
        try:
            debug_dir = Path.home() / ".obra" / "debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_file = debug_dir / f"parse_error_{int(time.time())}.txt"
            debug_file.write_text(
                f"Error Type: {error_type}\n\n"
                f"Diagnostic: {diagnostic}\n\n"
                f"Raw Response:\n{raw_response}\n",
                encoding="utf-8"
            )
            logger.info(f"Full parse error details saved to: {debug_file}")
            debug_path_info = f"\n\nFull response saved to: {debug_file}"
        except Exception as e:
            logger.warning(f"Could not save debug file: {e}")
            debug_path_info = ""

        return [
            {
                "id": "T1",
                "item_type": "task",
                "title": "LLM Response Parse Error - Manual Review Required",
                "description": (
                    f"**Error**: {error_type}\n\n"
                    f"**Diagnostic**: {diagnostic}\n\n"
                    f"**Raw Response Preview**:\n```\n{response_preview}\n```"
                    f"{debug_path_info}\n\n"
                    f"**Next Steps**:\n"
                    f"1. Review the raw response in the debug file above\n"
                    f"2. Check LLM provider configuration (API key, model, endpoint)\n"
                    f"3. Verify the prompt format is compatible with the LLM\n"
                    f"4. Check for rate limiting or quota issues\n"
                    f"5. If using extended thinking, try without it\n"
                ),
                "acceptance_criteria": [
                    "Root cause identified",
                    "LLM returns valid JSON response",
                    "Plan items parse successfully"
                ],
                "dependencies": [],
                "work_phase": "explore",
            }
        ]

    def _generate_parse_error_diagnostic(
        self, error: json.JSONDecodeError, raw_response: str
    ) -> str:
        """Generate detailed diagnostic for JSON parse errors.

        Args:
            error: JSONDecodeError exception
            raw_response: Raw LLM response

        Returns:
            Diagnostic message
        """
        diagnostics = []

        # Check for common issues
        if not raw_response:
            diagnostics.append("• Response is completely empty")
        elif raw_response.strip().startswith("<"):
            diagnostics.append("• Response appears to be HTML/XML, not JSON")
        elif "error" in raw_response.lower() and "rate" in raw_response.lower():
            diagnostics.append("• Response may indicate rate limiting")
        elif "error" in raw_response.lower() and "auth" in raw_response.lower():
            diagnostics.append("• Response may indicate authentication failure")
        elif not raw_response.strip().startswith(("{", "[")):
            diagnostics.append(
                f"• Response starts with unexpected character: '{raw_response[0] if raw_response else 'N/A'}'"
            )

        # Add JSON error details
        diagnostics.append(f"• JSON error at line {error.lineno}, column {error.colno}")
        diagnostics.append(f"• Error message: {error.msg}")

        # Check response length
        if len(raw_response) > 10000:
            diagnostics.append(
                f"• Response is very large ({len(raw_response)} chars) - may have exceeded output limits"
            )

        return "\n".join(diagnostics) if diagnostics else "No specific diagnostic available"


__all__ = [
    "VALID_PHASES",
    "WORK_TYPES_NEEDING_EXPLORATION",
    "WORK_TYPE_KEYWORDS",
    "DerivationEngine",
    "DerivationResult",
]
