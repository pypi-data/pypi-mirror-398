"""Prompt Enricher - Tier 2 (Tactical Context) for Two-Tier Prompting Architecture.

This module enriches server-generated base prompts with local tactical context.
It finds the CLIENT_CONTEXT_MARKER in the base prompt and replaces it with:
- File structure summary
- Recent git commits
- Recent errors (if applicable)

Architecture Pattern:
- Server (Tier 1): BasePromptGenerator → Strategic prompts with marker
- Client (Tier 2): PromptEnricher → Injects tactical context at marker
- Result: Complete prompts with both strategic and tactical context

Privacy Protection:
    Tactical context (file contents, git messages, errors) is gathered locally
    and NEVER sent to the server. Only the enriched prompt goes to the local LLM.

Security:
    All context is sanitized using PromptSanitizer to prevent prompt injection
    from user-controlled content (README files, git messages, etc.).

Related:
- functions/src/prompt/base_prompt_generator.py (server-side Tier 1)
- docs/architecture/firebase-saas-two-tier-prompting.md
- docs/decisions/ADR-027-two-tier-prompting-architecture.md

Example:
    >>> enricher = PromptEnricher(Path("/path/to/project"))
    >>> base_prompt = "Task: Do something\\n\\n<!-- CLIENT: Inject local context here -->"
    >>> enriched = enricher.enrich(base_prompt)
    >>> "Working Directory:" in enriched
    True
"""

import logging
import subprocess
from pathlib import Path

from obra.security import PromptSanitizer

logger = logging.getLogger(__name__)


# Context injection marker (must match server-side constant)
CLIENT_CONTEXT_MARKER = "<!-- CLIENT: Inject local context here -->"


class PromptEnricher:
    """Enriches server-generated base prompts with local tactical context.

    This class implements Tier 2 of the two-tier prompting architecture.
    It takes a base prompt from the server (containing strategic context and
    CLIENT_CONTEXT_MARKER) and enriches it with local tactical context:
    - Working directory
    - File structure summary
    - Recent git commits
    - Recent errors (if provided)

    All context is sanitized to prevent prompt injection attacks.

    Attributes:
        _working_dir: Path to the project working directory
        _sanitizer: PromptSanitizer instance for security

    Example:
        >>> enricher = PromptEnricher(Path("/home/user/myproject"))
        >>> base = "# Task\\n\\n<!-- CLIENT: Inject local context here -->"
        >>> enriched = enricher.enrich(base)
        >>> "Working Directory:" in enriched
        True
    """

    def __init__(self, working_dir: Path) -> None:
        """Initialize PromptEnricher.

        Args:
            working_dir: Path to project working directory for context gathering
        """
        self._working_dir = working_dir
        self._sanitizer = PromptSanitizer(strict_mode=False, log_detections=True)

    def enrich(
        self,
        base_prompt: str,
        recent_errors: list[str] | None = None
    ) -> str:
        """Enrich base prompt with local tactical context.

        Finds CLIENT_CONTEXT_MARKER in the base prompt and replaces it with
        sanitized local context. If marker is not found, appends context to
        the end (graceful degradation).

        Args:
            base_prompt: Base prompt from server containing marker
            recent_errors: Optional list of recent error messages to include

        Returns:
            Enriched prompt with tactical context injected

        Example:
            >>> enricher = PromptEnricher(Path("."))
            >>> base = "Task\\n\\n<!-- CLIENT: Inject local context here -->"
            >>> result = enricher.enrich(base)
            >>> "Working Directory:" in result
            True
        """
        # Gather local context
        context = self._gather_context(recent_errors)

        # Sanitize context
        sanitized_context = self._sanitize(context)

        # Replace marker with context
        if CLIENT_CONTEXT_MARKER in base_prompt:
            enriched = base_prompt.replace(CLIENT_CONTEXT_MARKER, sanitized_context)
            logger.debug("Enriched prompt with local context at marker")
        else:
            # Graceful degradation: append if marker not found
            enriched = f"{base_prompt}\n\n# Local Context\n\n{sanitized_context}"
            logger.warning("CLIENT_CONTEXT_MARKER not found in base_prompt, appending context")

        return enriched

    def _gather_context(self, recent_errors: list[str] | None = None) -> str:
        """Gather local tactical context for prompt enrichment.

        Collects:
        - Working directory path
        - File structure summary (important files only)
        - Recent git commits (last 5)
        - Recent errors (if provided)

        Args:
            recent_errors: Optional list of recent error messages

        Returns:
            Formatted context string (NOT yet sanitized)

        Example:
            >>> enricher = PromptEnricher(Path("."))
            >>> context = enricher._gather_context()
            >>> "Working Directory:" in context
            True
        """
        sections = []

        # Working directory
        sections.append(f"**Working Directory**: {self._working_dir}")

        # File structure
        try:
            file_structure = self._get_file_structure()
            if file_structure:
                sections.append(f"**Key Files** ({len(file_structure)} files):")
                sections.append("```")
                sections.append("\n".join(file_structure[:30]))  # Limit to 30 files
                if len(file_structure) > 30:
                    sections.append(f"... and {len(file_structure) - 30} more files")
                sections.append("```")
        except Exception as e:
            logger.warning(f"Failed to gather file structure: {e}")

        # Recent git commits
        try:
            git_log = self._get_recent_commits(limit=5)
            if git_log:
                sections.append("**Recent Commits**:")
                sections.append("```")
                sections.append(git_log)
                sections.append("```")
        except Exception as e:
            logger.debug(f"Failed to gather git log: {e}")

        # Recent errors
        if recent_errors:
            sections.append("**Recent Errors**:")
            sections.append("```")
            sections.append("\n".join(recent_errors[:5]))  # Limit to 5 errors
            sections.append("```")

        return "\n\n".join(sections)

    def _sanitize(self, context: str) -> str:
        """Sanitize context string to prevent prompt injection.

        Uses PromptSanitizer to escape role tags and detect injection patterns.
        All user-controlled content (git messages, file names, errors) is
        sanitized before inclusion in the prompt.

        Args:
            context: Raw context string to sanitize

        Returns:
            Sanitized context safe for prompt inclusion

        Example:
            >>> enricher = PromptEnricher(Path("."))
            >>> raw = "<system>evil</system>"
            >>> clean = enricher._sanitize(raw)
            >>> "[system]" in clean
            True
        """
        return self._sanitizer.sanitize_string(context, context="prompt_enrichment")

    def _get_file_structure(self) -> list[str]:
        """Get list of important project files.

        Returns relative paths for important file types, excluding common
        build/cache directories.

        Returns:
            List of relative file paths (sorted)

        Example:
            >>> enricher = PromptEnricher(Path("."))
            >>> files = enricher._get_file_structure()
            >>> isinstance(files, list)
            True
        """
        important_files = []
        important_patterns = [
            "*.py",
            "*.js",
            "*.ts",
            "*.tsx",
            "*.jsx",
            "*.go",
            "*.rs",
            "*.java",
            "*.cpp",
            "*.c",
            "*.h",
            "package.json",
            "pyproject.toml",
            "requirements.txt",
            "Cargo.toml",
            "go.mod",
            "README.md",
            "Makefile",
            "Dockerfile",
            ".obra/config.yaml",
        ]

        # Directories to skip - EXPANDED to include more common large directories
        skip_dirs = {
            ".git",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "target",  # Rust
            "out",
            "functions",  # Firebase functions
            "docs",  # Documentation (can be large)
            "tests",  # Test directories (can be large)
            "test",
            ".tox",
            "coverage",
            ".coverage",
            "htmlcov",
            "site-packages",
            ".next",
            ".nuxt",
            "vendor",
        }

        max_files = 50

        # ISSUE-SIM-001 HOTFIX: Skip file structure gathering entirely for now
        # The recursive directory traversal can hang on large directories
        # TODO: Implement optimized file structure gathering with proper timeout
        logger.debug("File structure gathering skipped (ISSUE-SIM-001 hotfix)")
        return []

    def _get_recent_commits(self, limit: int = 5) -> str:
        """Get recent git commit messages.

        Args:
            limit: Maximum number of commits to retrieve

        Returns:
            Formatted git log string, or empty string if not a git repo

        Example:
            >>> enricher = PromptEnricher(Path("."))
            >>> log = enricher._get_recent_commits(limit=3)
            >>> isinstance(log, str)
            True
        """
        try:
            result = subprocess.run(
                ["git", "log", f"-{limit}", "--oneline", "--no-decorate"],
                check=False, cwd=self._working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            # Not a git repo or git command failed
            return ""

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Git not available or command timed out
            return ""
        except Exception as e:
            logger.debug(f"Git log failed: {e}")
            return ""


__all__ = ["CLIENT_CONTEXT_MARKER", "PromptEnricher"]
