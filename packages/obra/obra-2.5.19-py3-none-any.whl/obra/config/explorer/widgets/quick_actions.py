"""Quick Actions Bar widget.

A horizontal bar showing numbered shortcuts for common configuration actions.
"""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Button, Static


class QuickActionsBar(Static):
    """Quick actions bar showing numbered shortcuts [1] [2] [3].

    Provides visual indicators for keyboard shortcuts to common actions:
    - 1: Change LLM settings
    - 2/p: Change preset
    - 3: Jump to Features section
    """

    DEFAULT_CSS = """
    QuickActionsBar {
        height: 2;
        dock: top;
        padding: 0 1;
        background: $primary-background-darken-1;
    }

    QuickActionsBar Horizontal {
        height: 100%;
        align: left middle;
    }

    QuickActionsBar .quick-action {
        padding: 0 1;
        margin-right: 2;
        background: $surface;
        color: $text;
    }

    QuickActionsBar .quick-action:hover {
        background: $primary;
    }

    QuickActionsBar .quick-action-key {
        color: $accent;
        text-style: bold;
    }

    QuickActionsBar .quick-action-label {
        color: $text-muted;
    }
    """

    class ActionClicked(Message):
        """Posted when a quick action is clicked.

        Attributes:
            action: The action identifier (llm, preset, features)
        """

        def __init__(self, action: str) -> None:
            super().__init__()
            self.action = action

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._actions = [
            ("1", "LLM", "llm", "Change orchestrator/agent LLM"),
            ("2", "Preset", "preset", "Apply configuration preset"),
            ("3", "Features", "features", "Jump to feature toggles"),
        ]

    def compose(self) -> ComposeResult:
        """Create the quick action buttons."""
        with Horizontal():
            yield Static(
                "[bold]Quick Actions:[/bold]  ",
                classes="quick-actions-label",
            )
            for key, label, action_id, tooltip in self._actions:
                yield Button(
                    f"[{key}] {label}",
                    id=f"quick-{action_id}",
                    classes="quick-action",
                    variant="default",
                )
            # Add hint about p key for preset
            yield Static(
                "  [dim](p = preset, ? = help)[/dim]",
                classes="quick-actions-hint",
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks by posting action message."""
        button_id = event.button.id or ""
        if button_id.startswith("quick-"):
            action = button_id[6:]  # Remove "quick-" prefix
            self.post_message(self.ActionClicked(action))
