"""Help Overlay widget showing all keybindings.

Provides a modal overlay displaying all available keyboard shortcuts.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, Static

# Keybinding definitions organized by category
KEYBINDINGS = {
    "Navigation": [
        ("Up / k", "Move selection up"),
        ("Down / j", "Move selection down"),
        ("Right / l", "Expand node / enter"),
        ("Left / h", "Collapse node / parent"),
        ("Enter", "Toggle boolean / Edit value"),
        ("Space", "Expand / Collapse node"),
    ],
    "Quick Actions": [
        ("1", "Change LLM provider/model"),
        ("2 / p", "Switch preset"),
        ("3", "Jump to Features section"),
    ],
    "Search & Filter": [
        ("/", "Enter search mode"),
        ("Esc", "Clear search / Cancel"),
    ],
    "File Operations": [
        ("s", "Save changes"),
        ("r", "Refresh from server"),
        ("R", "Reset selected to default"),
    ],
    "General": [
        ("?", "Show this help"),
        ("q", "Quit"),
    ],
}


class HelpOverlay(ModalScreen[None]):
    """Modal overlay showing all available keybindings."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("question_mark", "dismiss", "Close", show=False),
        Binding("q", "dismiss", "Close", show=False),
    ]

    DEFAULT_CSS = """
    HelpOverlay {
        align: center middle;
    }

    HelpOverlay > Container {
        width: 70;
        height: auto;
        max-height: 85%;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    HelpOverlay #title {
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    HelpOverlay .category {
        margin-top: 1;
        margin-bottom: 0;
        color: $accent;
        text-style: bold;
    }

    HelpOverlay .keybinding-row {
        padding: 0 1;
    }

    HelpOverlay .key {
        color: $primary;
        min-width: 12;
    }

    HelpOverlay .desc {
        color: $text;
    }

    HelpOverlay #footer {
        margin-top: 1;
        text-align: center;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the help overlay content."""
        with Container():
            yield Label("Keyboard Shortcuts", id="title")

            with Vertical():
                for category, bindings in KEYBINDINGS.items():
                    yield Static(f"-- {category} --", classes="category")
                    for key, description in bindings:
                        yield Static(
                            f"  [bold]{key:12}[/bold] {description}",
                            classes="keybinding-row",
                        )

                # Add configuration explanation
                yield Static("-- About Configuration --", classes="category")
                yield Static(
                    "  [bold]Local Settings[/bold] - Stored in ~/.obra/client-config.yaml",
                    classes="keybinding-row",
                )
                yield Static(
                    "    Changes apply immediately to this machine only.",
                    classes="keybinding-row",
                )
                yield Static(
                    "  [bold]Server Settings[/bold] - Stored in Obra cloud",
                    classes="keybinding-row",
                )
                yield Static(
                    "    Synced across all your devices via your account.",
                    classes="keybinding-row",
                )

            yield Static("Press Esc or ? to close", id="footer")

    def action_dismiss(self) -> None:
        """Close the help overlay."""
        self.dismiss(None)
