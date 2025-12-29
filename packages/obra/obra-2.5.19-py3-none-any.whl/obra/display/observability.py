"""Observability infrastructure for Obra CLI operations.

This module provides progressive verbosity levels and progress emission
for CLI commands, allowing users to observe LLM streaming, orchestration
phases, and execution progress in real-time.

Verbosity Levels:
    0 (QUIET): Minimal output - final results only
    1 (PROGRESS): Phase transitions with timestamps
    2 (DETAIL): Item-level details and LLM summaries
    3 (DEBUG): Full protocol info and debug messages

Usage:
    config = ObservabilityConfig(verbosity=VerbosityLevel.PROGRESS, stream=True)
    emitter = ProgressEmitter(config, console)
    emitter.phase_started("DERIVATION")
    emitter.llm_streaming("Here is my response...")
    emitter.phase_completed("DERIVATION", duration_ms=1500)

Security:
    - NEVER emit user prompts or LLM system prompts (IP protection)
    - NEVER emit API keys, credentials, or secrets
    - LLM responses are safe to show (user-requested observability)
"""

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum

from rich.console import Console


class VerbosityLevel(IntEnum):
    """Progressive verbosity levels for CLI output.

    Attributes:
        QUIET: Minimal output - final results only
        PROGRESS: Phase transitions with timestamps
        DETAIL: Item-level details and LLM summaries
        DEBUG: Full protocol info and debug messages
    """

    QUIET = 0
    PROGRESS = 1
    DETAIL = 2
    DEBUG = 3


@dataclass
class ObservabilityConfig:
    """Configuration for CLI observability features.

    Attributes:
        verbosity: Output detail level (0-3)
        stream: Whether to show LLM responses as they stream
        timestamps: Whether to include timestamps in output
    """

    verbosity: int = VerbosityLevel.QUIET
    stream: bool = False
    timestamps: bool = True


class ProgressEmitter:
    """Emits progress events based on observability configuration.

    This class formats and displays orchestration progress events according
    to the configured verbosity level, supporting real-time LLM streaming
    and progressive detail disclosure.

    Attributes:
        config: Observability configuration (None uses defaults)
        console: Rich Console for formatted output
    """

    def __init__(
        self, config: ObservabilityConfig | None, console: Console
    ) -> None:
        """Initialize the progress emitter.

        Args:
            config: Observability config, or None for defaults
            console: Rich Console instance for output
        """
        self.config = config or ObservabilityConfig()
        self.console = console
        self._is_tty = console.is_terminal

    def _timestamp(self) -> str:
        """Get current timestamp in [HH:MM:SS] format.

        Returns:
            Formatted timestamp string if timestamps enabled, empty string otherwise
        """
        if self.config.timestamps:
            return f"[{datetime.now().strftime('%H:%M:%S')}] "
        return ""

    def _print(
        self, message: str, style: str | None = None, end: str = "\n"
    ) -> None:
        """Print message with or without Rich formatting based on TTY detection.

        Args:
            message: Message to print
            style: Rich style to apply (only if TTY)
            end: String appended after the message (default: newline)
        """
        if self._is_tty and style:
            self.console.print(message, style=style, end=end)
        else:
            # Plain text output for non-TTY (CI, piped output)
            # Always use console.print to respect the console's file output
            self.console.print(message, end=end)

    def phase_started(self, phase: str, context: dict | None = None) -> None:
        """Emit event when an orchestration phase starts.

        Args:
            phase: Phase name (e.g., "DERIVATION", "REFINEMENT", "EXECUTION")
            context: Optional context information about the phase
        """
        # Level 0 (QUIET): Show minimal phase indicator
        if self.config.verbosity == VerbosityLevel.QUIET:
            phase_label = {
                "DERIVATION": "Deriving plan",
                "REFINEMENT": "Examining plan",
                "EXECUTION": "Executing",
            }.get(phase, phase)
            self._print(f"{phase_label}...", end="")
            return

        # Level 1+ (PROGRESS and above): Show with timestamp
        if self.config.verbosity < VerbosityLevel.PROGRESS:
            return

        timestamp = self._timestamp()
        self._print(f"{timestamp}Phase: {phase}", style="bold cyan")

        if self.config.verbosity >= VerbosityLevel.DEBUG and context:
            self._print(f"[DEBUG] Context: {context}", style="dim")

    def phase_completed(
        self, phase: str, result: dict | None = None, duration_ms: int = 0
    ) -> None:
        """Emit event when an orchestration phase completes.

        Args:
            phase: Phase name that completed
            result: Optional result data from the phase
            duration_ms: Phase duration in milliseconds
        """
        # Level 0 (QUIET): Complete the line with result count
        if self.config.verbosity == VerbosityLevel.QUIET:
            if result and "item_count" in result:
                item_count = result["item_count"]
                self._print(f" done ({item_count} items)")
            elif result and "issue_count" in result:
                issue_count = result["issue_count"]
                self._print(f" done ({issue_count} issues)")
            else:
                self._print(" done")
            return

        # Level 1+ (PROGRESS and above): Show with timestamp and duration
        if self.config.verbosity < VerbosityLevel.PROGRESS:
            return

        timestamp = self._timestamp()
        duration_sec = duration_ms / 1000.0

        # Build completion message with item count if available
        if result and "item_count" in result:
            item_count = result["item_count"]
            message = f"{timestamp}"
            if phase == "DERIVATION":
                message += f"Derived {item_count} plan items ({duration_sec:.1f}s)"
            elif phase == "REFINEMENT":
                issues = result.get("issue_count", 0)
                message += f"Found {issues} issues ({duration_sec:.1f}s)"
            else:
                message += f"Phase {phase} complete ({duration_sec:.1f}s)"
            self._print(message, style="green")

            # At PROGRESS level, show item list if available
            if self.config.verbosity == VerbosityLevel.PROGRESS and "items" in result:
                for item in result["items"]:
                    item_id = item.get("id", "?")
                    item_title = item.get("title", "untitled")
                    self._print(f"           {item_id}: {item_title}")
        else:
            self._print(
                f"{timestamp}Phase {phase} complete ({duration_sec:.1f}s)",
                style="green",
            )

        if self.config.verbosity >= VerbosityLevel.DETAIL and result:
            # Show result summary at detail level
            if "items" in result and self.config.verbosity > VerbosityLevel.PROGRESS:
                # Show detailed plan items with descriptions and dependencies
                for item in result["items"]:
                    item_id = item.get("id", "?")
                    item_title = item.get("title", "untitled")
                    depends_on = item.get("depends_on", [])

                    # Show item with dependency info
                    if depends_on:
                        deps_str = ", ".join(depends_on)
                        self._print(f"  {item_id}: {item_title} (depends: {deps_str})")
                    else:
                        self._print(f"  {item_id}: {item_title}")

                    # Show description or acceptance criteria if available
                    description = item.get("description", "")
                    acceptance_criteria = item.get("acceptance_criteria", [])

                    if description:
                        # Multi-line description - show indented
                        for line in description.split("\n"):
                            if line.strip():
                                self._print(f"      - {line.strip()}", style="dim")
                    elif acceptance_criteria:
                        # Show acceptance criteria as bullet points
                        for criterion in acceptance_criteria:
                            self._print(f"      - {criterion}", style="dim")

        if self.config.verbosity >= VerbosityLevel.DEBUG and result:
            self._print(f"[DEBUG] Full result: {result}", style="dim")

    def llm_started(self, purpose: str) -> None:
        """Emit event when an LLM invocation starts.

        Args:
            purpose: Description of what the LLM is being asked to do
        """
        if self.config.verbosity < VerbosityLevel.DETAIL:
            return

        timestamp = self._timestamp()
        self._print(f"{timestamp}LLM invocation: {purpose}", style="yellow")

    def llm_streaming(self, chunk: str) -> None:
        """Emit LLM response chunk during streaming.

        Args:
            chunk: Text chunk from the streaming LLM response
        """
        if not self.config.stream:
            return

        # Stream output with [LLM] prefix
        # Don't add timestamp per chunk (would be noisy)
        if self._is_tty:
            self.console.print(f"  [LLM] {chunk}", end="", style="blue")
        else:
            # Line-by-line for non-TTY (no streaming animation)
            self.console.print(f"  [LLM] {chunk}")

    def llm_completed(self, summary: str, tokens: int = 0) -> None:
        """Emit event when an LLM invocation completes.

        Args:
            summary: Summary of the LLM response
            tokens: Token count for the response
        """
        if self.config.verbosity < VerbosityLevel.DETAIL:
            return

        timestamp = self._timestamp()
        token_info = f" ({tokens} tokens)" if tokens > 0 else ""
        self._print(
            f"{timestamp}LLM complete{token_info}: {summary}", style="green"
        )

        if self.config.verbosity >= VerbosityLevel.DEBUG:
            self._print(f"[DEBUG] Token count: {tokens}", style="dim")

    def item_started(self, item: dict) -> None:
        """Emit event when processing a plan item starts.

        Args:
            item: Plan item being processed
        """
        item_id = item.get("id", "?")

        # Level 0 (QUIET): Show minimal "Executing TX..."
        if self.config.verbosity == VerbosityLevel.QUIET:
            self._print(f"Executing {item_id}...", end="")
            return

        # Level 1 (PROGRESS): Show item with title
        if self.config.verbosity == VerbosityLevel.PROGRESS:
            timestamp = self._timestamp()
            item_title = item.get("title", "")
            if item_title:
                self._print(f"{timestamp}Executing {item_id}: {item_title}...", style="cyan")
            else:
                self._print(f"{timestamp}Executing {item_id}...", style="cyan")
            return

        # Level 2+ (DETAIL and above): Show full details
        timestamp = self._timestamp()
        item_title = item.get("title", "untitled")
        self._print(f"{timestamp}Item {item_id}: {item_title}", style="cyan")

        if self.config.verbosity >= VerbosityLevel.DEBUG:
            self._print(f"[DEBUG] Full item: {item}", style="dim")

    def item_completed(self, item: dict, result: dict | None = None) -> None:
        """Emit event when processing a plan item completes.

        Args:
            item: Plan item that was processed
            result: Optional result data from processing
        """
        item_id = item.get("id", "?")

        # Level 0 (QUIET): Complete the line with " done"
        if self.config.verbosity == VerbosityLevel.QUIET:
            self._print(" done")
            return

        # Level 1 (PROGRESS): Show completion with timestamp
        if self.config.verbosity == VerbosityLevel.PROGRESS:
            timestamp = self._timestamp()
            self._print(f"{timestamp}{item_id} complete", style="green")
            return

        # Level 2+ (DETAIL and above): Show full details
        timestamp = self._timestamp()
        self._print(f"{timestamp}Item {item_id} complete", style="green")

        if self.config.verbosity >= VerbosityLevel.DEBUG and result:
            self._print(f"[DEBUG] Result: {result}", style="dim")

    def error(
        self,
        message: str,
        hint: str | None = None,
        phase: str | None = None,
        affected_items: list | None = None,
        stack_trace: str | None = None,
        raw_response: dict | None = None,
    ) -> None:
        """Display error with detail based on verbosity level.

        Args:
            message: Error message
            hint: Recovery hint (shown at all levels)
            phase: Current phase when error occurred (shown at PROGRESS+)
            affected_items: Plan items affected by error (shown at DETAIL+)
            stack_trace: Full stack trace (shown at DEBUG only)
            raw_response: Raw server/LLM response (shown at DEBUG only)
        """
        timestamp = self._timestamp()

        # Level 0 (QUIET): Basic error + hint
        self._print(f"Error: {message}", style="bold red")
        if hint:
            self._print(f"Hint: {hint}", style="yellow")

        # Level 1 (PROGRESS): + timestamp + phase context
        if self.config.verbosity >= VerbosityLevel.PROGRESS:
            if timestamp:
                self._print(f"{timestamp}Error occurred", style="dim")
            if phase:
                self._print(f"Phase: {phase}", style="dim")

        # Level 2 (DETAIL): + affected items + partial results
        if self.config.verbosity >= VerbosityLevel.DETAIL and affected_items:
            self._print("Affected items:", style="yellow")
            for item in affected_items:
                item_id = item.get("id", "?")
                item_title = item.get("title", "unknown")
                self._print(f"  - {item_id}: {item_title}", style="dim")

        # Level 3 (DEBUG): + stack trace + raw response
        if self.config.verbosity >= VerbosityLevel.DEBUG:
            if stack_trace:
                self._print("[DEBUG] Stack trace:", style="dim")
                for line in stack_trace.split("\n"):
                    if line.strip():
                        self._print(f"  {line}", style="dim")
            if raw_response:
                self._print(f"[DEBUG] Raw response: {raw_response}", style="dim")
