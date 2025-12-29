"""Claude Code agent for implementation tasks.

This module provides ClaudeCodeAgent, which wraps Claude Code CLI for
executing implementation tasks. Unlike review agents, Claude Code is used
for code generation and modification.

Architecture:
    - Runs Claude Code CLI in headless --print mode
    - Session persistence via --session-id
    - Dangerous mode for automated orchestration
    - JSON output parsing for structured responses

Usage:
    The ClaudeCodeAgent is used by the Execute handler for plan item execution.
    It is NOT a review agent (does not inherit from BaseAgent).

Example:
    >>> agent = ClaudeCodeAgent(Path("/workspace"))
    >>> agent.initialize({"response_timeout": 7200})
    >>> response = agent.send_prompt("Implement the login function")
    >>> print(response)

Related:
    - src/agents/claude_code_local.py (original implementation)
    - obra/hybrid/handlers/execute.py
"""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from obra.exceptions import ExecutionError

logger = logging.getLogger(__name__)


class ClaudeCodeAgent:
    """Claude Code agent for implementation tasks.

    Uses subprocess.run() to execute Claude Code CLI with --print flag for
    non-interactive, stateless operation.

    Key Features:
        - Stateless subprocess calls (no persistent process)
        - Session persistence via --session-id (optional)
        - Dangerous mode for automated orchestration
        - JSON output parsing for structured responses
        - Retry logic for session-in-use errors

    Attributes:
        cli_command: Command to launch Claude Code CLI
        workspace_path: Path to workspace directory
        session_id: UUID for session persistence
        response_timeout: Timeout in seconds
        bypass_permissions: Enable dangerous mode
    """

    def __init__(self, workspace_path: Path | None = None) -> None:
        """Initialize Claude Code agent.

        Args:
            workspace_path: Path to workspace directory (optional, can set in initialize)
        """
        self.cli_command: str = "claude"
        self.workspace_path: Path | None = workspace_path
        self.session_id: str | None = None
        self.response_timeout: int = 7200  # 2 hours default
        self.environment_vars: dict[str, str] = {}
        self.use_session_persistence: bool = False
        self.max_retries: int = 5
        self.retry_initial_delay: float = 2.0
        self.retry_backoff: float = 1.5
        self.bypass_permissions: bool = True
        self.last_metadata: dict[str, Any] | None = None

        # Headless mode instruction
        self.headless_instruction: str = (
            "[HEADLESS MODE - CRITICAL CONSTRAINT]\n"
            "You are running as an automated subprocess with NO stdin (no human present).\n"
            "Interactive tools WILL FAIL. This constraint OVERRIDES all other behaviors.\n\n"
            "PROHIBITED (will cause task failure):\n"
            "- AskUserQuestion or ANY interactive/question tools\n"
            "- Any tool requiring keyboard input or navigation\n"
            "- Pausing for user confirmation\n\n"
            "REQUIRED:\n"
            "- State assumptions and proceed autonomously\n"
            "- Make reasonable decisions from task context\n"
            "- If blocked, explain what's needed in your response\n\n"
        )

        logger.info("ClaudeCodeAgent initialized")

    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize agent with configuration.

        Args:
            config: Configuration dict containing:
                - workspace_path: Path to workspace (required if not set in __init__)
                - cli_command: Command to run (default: 'claude')
                - response_timeout: Seconds to wait (default: 7200)
                - use_session_persistence: Reuse session ID (default: False)
                - bypass_permissions: Enable dangerous mode (default: True)

        Raises:
            ExecutionError: If configuration is invalid
        """
        # Handle nested config
        if "local" in config and isinstance(config["local"], dict):
            config = config["local"]

        # Extract workspace path
        workspace = config.get("workspace_path") or config.get("workspace_dir")
        if workspace:
            self.workspace_path = Path(workspace)
        elif self.workspace_path is None:
            raise ExecutionError(
                "Missing required config: workspace_path",
                recovery="Provide workspace_path in agent configuration",
            )

        # Extract other config - resolve full path for Windows compatibility
        cli_name = config.get("cli_command") or config.get("command", "claude")
        self.cli_command = shutil.which(cli_name) or cli_name
        self.response_timeout = config.get("response_timeout", 7200)
        self.use_session_persistence = config.get("use_session_persistence", False)
        self.bypass_permissions = config.get("bypass_permissions", True)

        # Generate session ID if persistence enabled
        if self.use_session_persistence:
            self.session_id = str(uuid.uuid4())
            logger.info(f"Session persistence enabled: {self.session_id}")
        else:
            self.session_id = None

        # Create workspace if needed
        if self.workspace_path:
            self.workspace_path.mkdir(parents=True, exist_ok=True)

        # Prepare environment
        self.environment_vars = {
            "DISABLE_AUTOUPDATER": "1",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "true",
            "TERM": os.environ.get("TERM", "xterm-256color"),
            "PATH": os.environ.get("PATH", ""),
        }

        # Verify CLI is available
        if not self.is_healthy():
            raise ExecutionError(
                f"Claude Code CLI not working: {self.cli_command}",
                recovery="Ensure Claude Code CLI is properly installed and authenticated",
            )

        logger.info(f"Initialized agent: workspace={self.workspace_path}")

    def send_prompt(self, prompt: str, context: dict | None = None) -> str:
        """Send prompt to Claude Code and return response.

        Args:
            prompt: The prompt text to send
            context: Optional context dict with:
                - working_directory: Project working directory (overrides workspace_path)
                - max_turns: Maximum turns for conversation

        Returns:
            Complete response from Claude Code

        Raises:
            ExecutionError: If Claude fails or returns error
        """
        if self.workspace_path is None:
            raise ExecutionError(
                "Agent not initialized",
                recovery="Call initialize() before sending prompts",
            )

        # Extract working directory from context (project's working_directory)
        # Fix for ISSUE-AGENT-001: Use context working_directory when provided
        working_dir: Path | None = None
        if context and context.get("working_directory"):
            working_dir = Path(context["working_directory"])
            logger.debug(f"Using project working directory: {working_dir}")

        # Generate session ID
        if self.session_id:
            session_id = self.session_id
        else:
            session_id = str(uuid.uuid4())
            if self.use_session_persistence:
                self.session_id = session_id

        # Build arguments
        args = [
            "--print",
            "--session-id",
            session_id,
            "--output-format",
            "json",
        ]

        # Add max_turns if provided
        if context and "max_turns" in context:
            args.extend(["--max-turns", str(context["max_turns"])])

        # Add dangerous mode flag
        if self.bypass_permissions:
            args.append("--dangerously-skip-permissions")

        # Prepend headless instruction
        full_prompt = self.headless_instruction + prompt
        args.append(full_prompt)

        logger.info(f"CLAUDE_SEND: prompt_chars={len(prompt):,}, session={session_id[:8]}...")

        # Retry logic
        retry_delay = self.retry_initial_delay

        for attempt in range(self.max_retries):
            # Execute command with project's working directory if provided
            result = self._run_claude(args, working_dir=working_dir)

            if result.returncode == 0:
                return self._parse_response(result.stdout.strip(), context)

            # Check for session-in-use error
            if "already in use" in result.stderr.lower():
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"Session in use, retrying in {retry_delay:.1f}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(retry_delay)
                    retry_delay *= self.retry_backoff
                    continue
                raise ExecutionError(
                    f"Session still in use after {self.max_retries} retries",
                    recovery="Wait longer between calls or use fresh sessions",
                )

            # Other error
            raise ExecutionError(
                f"Claude failed with exit code {result.returncode}",
                exit_code=result.returncode,
                stderr=result.stderr,
            )

        raise ExecutionError("Unexpected error in send_prompt retry loop")

    def _run_claude(
        self, args: list[str], working_dir: Path | None = None
    ) -> subprocess.CompletedProcess:
        """Run claude command.

        Args:
            args: Arguments to pass to claude
            working_dir: Optional working directory override (project's working_directory)

        Returns:
            CompletedProcess with stdout, stderr, returncode
        """
        command = [self.cli_command] + args
        env = os.environ.copy()
        env.update(self.environment_vars)

        # Use working_dir if provided, otherwise fall back to workspace_path (ISSUE-AGENT-001)
        cwd = working_dir if working_dir else self.workspace_path

        try:
            return subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=self.response_timeout,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise ExecutionError(
                f"Timeout after {self.response_timeout}s",
                recovery="Increase response_timeout in config",
            )
        except FileNotFoundError:
            raise ExecutionError(
                f"Claude command not found: {self.cli_command}",
                recovery="Install Claude Code CLI or specify correct path in config",
            )

    def _parse_response(
        self,
        raw_response: str,
        context: dict | None = None,
    ) -> str:
        """Parse JSON response from Claude.

        Args:
            raw_response: Raw response string
            context: Optional context for error handling

        Returns:
            Extracted result text
        """
        try:
            json_response = json.loads(raw_response)
            result_text = json_response.get("result", "")
            self.last_metadata = self._extract_metadata(json_response)

            # Check for max_turns error
            if self.last_metadata.get("subtype") == "error_max_turns":
                num_turns = self.last_metadata.get("num_turns", 0)
                max_turns = context.get("max_turns") if context else None
                raise ExecutionError(
                    f"Task exceeded max_turns limit ({num_turns}/{max_turns})",
                    recovery="Retry with increased max_turns or break task into smaller pieces",
                )

            return result_text

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed: {e}")
            self.last_metadata = None
            return raw_response

    def _extract_metadata(self, response: dict[str, Any]) -> dict[str, Any]:
        """Extract metadata from Claude JSON response."""
        usage = response.get("usage", {})

        total_tokens = (
            usage.get("input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
            + usage.get("output_tokens", 0)
        )

        return {
            "type": response.get("type"),
            "subtype": response.get("subtype"),
            "session_id": response.get("session_id"),
            "total_tokens": total_tokens,
            "duration_ms": response.get("duration_ms", 0),
            "num_turns": response.get("num_turns", 0),
        }

    def get_last_metadata(self) -> dict[str, Any] | None:
        """Get metadata from last send_prompt() call."""
        return self.last_metadata

    def is_healthy(self) -> bool:
        """Check if Claude Code is available."""
        try:
            result = subprocess.run(
                [self.cli_command, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_status(self) -> dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_type": "claude-code",
            "mode": "headless",
            "session_id": self.session_id,
            "workspace": str(self.workspace_path) if self.workspace_path else None,
            "command": self.cli_command,
            "healthy": self.is_healthy(),
        }

    def get_workspace_files(self) -> list[Path]:
        """Get list of files in workspace."""
        if not self.workspace_path or not self.workspace_path.exists():
            return []

        files = []
        ignore_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}

        for item in self.workspace_path.rglob("*"):
            if item.is_file():
                if not any(p in item.parts for p in ignore_dirs):
                    files.append(item)
        return files

    def read_file(self, path: Path) -> str:
        """Read file from workspace."""
        if not path.is_absolute() and self.workspace_path:
            path = self.workspace_path / path
        return path.read_text()

    def write_file(self, path: Path, content: str) -> None:
        """Write file to workspace."""
        if not path.is_absolute() and self.workspace_path:
            path = self.workspace_path / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def get_file_changes(self, since: float | None = None) -> list[dict]:
        """Get files modified since timestamp."""
        changes = []

        if not self.workspace_path or not self.workspace_path.exists():
            return changes

        for file_path in self.get_workspace_files():
            stat = file_path.stat()
            if since is not None and stat.st_mtime < since:
                continue

            try:
                content = file_path.read_bytes()
                file_hash = hashlib.sha256(content).hexdigest()
            except Exception:
                file_hash = "unknown"

            changes.append({
                "path": file_path,
                "change_type": "modified",
                "timestamp": stat.st_mtime,
                "hash": file_hash,
                "size": stat.st_size,
            })

        return changes

    def cleanup(self) -> None:
        """Clean up agent resources."""
        logger.info("ClaudeCodeAgent cleanup complete")


__all__ = ["ClaudeCodeAgent"]
