"""Search Bar widget for filtering the configuration tree.

Provides a search/filter input that filters the tree view to show
only nodes matching the search query.
"""

from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Input, Label, Static


class SearchBar(Static):
    """Search bar widget for filtering the configuration tree.

    Shows an input field when activated, filters tree nodes by path/key.
    """

    BINDINGS = [
        Binding("escape", "cancel_search", "Cancel", priority=True),
        Binding("enter", "apply_search", "Filter", priority=True),
    ]

    DEFAULT_CSS = """
    SearchBar {
        height: 3;
        display: none;
        padding: 0 1;
        background: $surface;
        border-bottom: solid $primary;
    }

    SearchBar.visible {
        display: block;
    }

    SearchBar Horizontal {
        height: 3;
        align: left middle;
    }

    SearchBar Label {
        padding: 0 1;
        text-style: bold;
    }

    SearchBar Input {
        width: 1fr;
    }

    SearchBar .hint {
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the search bar."""
        super().__init__(*args, **kwargs)
        self._active = False
        self._query = ""

    def compose(self) -> ComposeResult:
        """Create the search bar content."""
        with Horizontal():
            yield Label("Search:")
            yield Input(placeholder="Type to filter settings...", id="search-input")
            yield Static("Enter to filter, Esc to cancel", classes="hint")

    @property
    def is_active(self) -> bool:
        """Check if the search bar is currently active."""
        return self._active

    @property
    def search_query(self) -> str:
        """Get the current search query."""
        return self._query

    def activate(self) -> None:
        """Show and focus the search bar."""
        self._active = True
        self.add_class("visible")
        try:
            input_widget = self.query_one("#search-input", Input)
            input_widget.value = ""
            input_widget.focus()
        except Exception:
            pass

    def deactivate(self) -> None:
        """Hide the search bar and clear filter."""
        self._active = False
        self._query = ""
        self.remove_class("visible")
        # Post message to clear filter
        self.post_message(self.SearchCleared())

    def action_cancel_search(self) -> None:
        """Cancel search and hide the bar."""
        self.deactivate()

    def action_apply_search(self) -> None:
        """Apply the current search query."""
        try:
            input_widget = self.query_one("#search-input", Input)
            self._query = input_widget.value.strip()

            if self._query:
                self.post_message(self.SearchApplied(self._query))
            else:
                self.deactivate()
        except Exception:
            self.deactivate()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for live filtering."""
        # Post message for live filtering as user types
        query = event.value.strip()
        if query:
            self.post_message(self.SearchChanged(query))
        else:
            self.post_message(self.SearchCleared())

    class SearchApplied(Message):
        """Message posted when search is submitted (Enter pressed)."""

        def __init__(self, query: str) -> None:
            super().__init__()
            self.query = query

    class SearchChanged(Message):
        """Message posted when search input changes (live filtering)."""

        def __init__(self, query: str) -> None:
            super().__init__()
            self.query = query

    class SearchCleared(Message):
        """Message posted when search is cleared/cancelled."""

