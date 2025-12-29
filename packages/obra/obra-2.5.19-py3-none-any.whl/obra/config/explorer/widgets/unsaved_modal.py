"""Unsaved Changes Modal widget.

Prompts user when quitting with pending changes, offering options to
save, discard, or cancel the quit action.
"""

from enum import Enum

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class UnsavedAction(Enum):
    """User's choice for handling unsaved changes."""

    SAVE = "save"  # Save changes then quit
    DISCARD = "discard"  # Discard changes and quit
    CANCEL = "cancel"  # Cancel quit, stay in app


class UnsavedChangesModal(ModalScreen[UnsavedAction]):
    """Modal dialog shown when user tries to quit with unsaved changes.

    Offers three options:
    - [s] Save: Save changes and then quit
    - [q] Quit: Discard changes and quit
    - [c] Cancel: Stay in the application
    """

    BINDINGS = [
        Binding("s", "save", "Save & Quit", priority=True),
        Binding("q", "discard", "Discard & Quit", priority=True),
        Binding("c", "cancel", "Cancel", priority=True),
        Binding("escape", "cancel", "Cancel", priority=True, show=False),
    ]

    DEFAULT_CSS = """
    UnsavedChangesModal {
        align: center middle;
    }

    UnsavedChangesModal > Container {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $warning;
        padding: 1 2;
    }

    UnsavedChangesModal #title {
        text-style: bold;
        color: $warning;
        margin-bottom: 1;
    }

    UnsavedChangesModal #message {
        margin-bottom: 1;
    }

    UnsavedChangesModal #change-count {
        color: $primary;
        margin-bottom: 1;
    }

    UnsavedChangesModal .buttons {
        height: 3;
        align: center middle;
    }

    UnsavedChangesModal Button {
        margin: 0 1;
    }

    UnsavedChangesModal #save-btn {
        border: tall $success;
    }

    UnsavedChangesModal #discard-btn {
        border: tall $error;
    }
    """

    def __init__(self, pending_count: int = 0) -> None:
        """Initialize the unsaved changes modal.

        Args:
            pending_count: Number of unsaved changes
        """
        super().__init__()
        self._pending_count = pending_count

    def compose(self) -> ComposeResult:
        """Create the modal content."""
        with Container():
            yield Label("Unsaved Changes", id="title")
            yield Static(
                "You have unsaved changes. What would you like to do?",
                id="message",
            )
            suffix = "s" if self._pending_count != 1 else ""
            yield Static(
                f"[bold]{self._pending_count}[/bold] pending change{suffix}",
                id="change-count",
            )

            with Horizontal(classes="buttons"):
                yield Button("[s] Save & Quit", variant="success", id="save-btn")
                yield Button("[q] Discard", variant="error", id="discard-btn")
                yield Button("[c] Cancel", variant="default", id="cancel-btn")

    def action_save(self) -> None:
        """Save changes then quit."""
        self.dismiss(UnsavedAction.SAVE)

    def action_discard(self) -> None:
        """Discard changes and quit."""
        self.dismiss(UnsavedAction.DISCARD)

    def action_cancel(self) -> None:
        """Cancel quit and stay in app."""
        self.dismiss(UnsavedAction.CANCEL)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "save-btn":
            self.action_save()
        elif event.button.id == "discard-btn":
            self.action_discard()
        elif event.button.id == "cancel-btn":
            self.action_cancel()
