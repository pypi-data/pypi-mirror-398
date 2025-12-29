"""Preset Picker modal for configuration presets.

Provides a modal dialog for selecting configuration presets with
comparison view showing what each preset includes.
"""

from dataclasses import dataclass
from typing import Any, Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Label, OptionList, Static
from textual.widgets.option_list import Option

# Preset definitions with descriptions and feature toggles
PRESETS: dict[str, dict[str, Any]] = {
    "beta-tester-default": {
        "name": "Beta Tester Default",
        "description": "Balanced settings for beta testing",
        "features": {
            "budgets.enabled": True,
            "rca_agent.enabled": True,
            "security_audit.enabled": False,
            "auto_commit.enabled": False,
        },
    },
    "power-user": {
        "name": "Power User",
        "description": "All features enabled, aggressive automation",
        "features": {
            "budgets.enabled": True,
            "rca_agent.enabled": True,
            "security_audit.enabled": True,
            "auto_commit.enabled": True,
        },
    },
    "conservative": {
        "name": "Conservative",
        "description": "Minimal automation, maximum human control",
        "features": {
            "budgets.enabled": False,
            "rca_agent.enabled": False,
            "security_audit.enabled": False,
            "auto_commit.enabled": False,
        },
    },
}


@dataclass
class PresetSelection:
    """Result of preset picker selection."""

    preset_id: str
    preset_name: str
    features: dict[str, Any]


class PresetPicker(ModalScreen[Optional[PresetSelection]]):
    """Modal dialog for selecting configuration presets.

    Shows available presets with descriptions and a comparison view
    of what features each preset enables/disables.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "apply", "Apply", priority=True),
        Binding("tab", "compare", "Compare", show=False),
    ]

    DEFAULT_CSS = """
    PresetPicker {
        align: center middle;
    }

    PresetPicker > Container {
        width: 75;
        height: auto;
        max-height: 25;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    PresetPicker #title {
        text-style: bold;
        width: 100%;
        text-align: center;
        margin-bottom: 1;
    }

    PresetPicker #description {
        color: $text-muted;
        margin-bottom: 1;
    }

    PresetPicker OptionList {
        height: auto;
        max-height: 8;
        margin-bottom: 1;
    }

    PresetPicker .buttons {
        height: 3;
        align: center middle;
    }

    PresetPicker Button {
        margin: 0 1;
    }

    PresetPicker #comparison {
        background: $surface-darken-1;
        padding: 1;
        margin-bottom: 1;
        height: auto;
        max-height: 10;
    }

    PresetPicker #comparison-title {
        text-style: bold;
        margin-bottom: 1;
    }

    PresetPicker .feature-enabled {
        color: $success;
    }

    PresetPicker .feature-disabled {
        color: $text-muted;
    }
    """

    def __init__(
        self,
        current_preset: str = "beta-tester-default",
    ) -> None:
        """Initialize the preset picker.

        Args:
            current_preset: Currently active preset ID
        """
        super().__init__()
        self._current_preset = current_preset
        self._selected_preset: str | None = None

    def compose(self) -> ComposeResult:
        """Create the modal content."""
        with Container():
            yield Label("Select Configuration Preset", id="title")
            yield Static(
                "Presets are curated configurations for different use cases.",
                id="description",
            )

            yield OptionList(id="presets")

            # Comparison panel
            with Vertical(id="comparison"):
                yield Static("Preset details:", id="comparison-title")
                yield Static("", id="comparison-content")

            with Horizontal(classes="buttons"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Apply", variant="primary", id="apply")

    def on_mount(self) -> None:
        """Initialize the preset list."""
        option_list = self.query_one("#presets", OptionList)

        for preset_id, preset_info in PRESETS.items():
            current_marker = " (current)" if preset_id == self._current_preset else ""
            label = f"[{preset_info['name']}]{current_marker} - {preset_info['description']}"
            option_list.add_option(Option(label, id=preset_id))

        option_list.focus()
        option_list.highlighted = 0
        self._update_comparison(list(PRESETS.keys())[0])

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        """Update comparison when selection changes."""
        if event.option and event.option.id:
            self._update_comparison(str(event.option.id))

    def _update_comparison(self, preset_id: str) -> None:
        """Update the comparison panel for a preset.

        Args:
            preset_id: ID of preset to show details for
        """
        self._selected_preset = preset_id
        preset = PRESETS.get(preset_id, {})
        features = preset.get("features", {})

        lines = []
        for feature, enabled in features.items():
            icon = "●" if enabled else "○"
            status = "enabled" if enabled else "disabled"
            # Format feature name nicely
            feature_name = feature.replace(".", " > ").replace("_", " ").title()
            lines.append(f"  {icon} {feature_name}: {status}")

        content = self.query_one("#comparison-content", Static)
        content.update("\n".join(lines) if lines else "No features defined")

    def action_cancel(self) -> None:
        """Cancel and close modal."""
        self.dismiss(None)

    def action_apply(self) -> None:
        """Apply selected preset and close modal."""
        if self._selected_preset:
            preset = PRESETS.get(self._selected_preset, {})
            self.dismiss(
                PresetSelection(
                    preset_id=self._selected_preset,
                    preset_name=preset.get("name", self._selected_preset),
                    features=preset.get("features", {}),
                )
            )

    def action_compare(self) -> None:
        """Toggle comparison view (placeholder for future side-by-side)."""
        # Future enhancement: show side-by-side comparison of all presets

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "cancel":
            self.action_cancel()
        elif event.button.id == "apply":
            self.action_apply()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option double-click/enter."""
        self.action_apply()

    class PresetChanged(Message):
        """Message posted when preset is changed."""

        def __init__(self, selection: PresetSelection) -> None:
            super().__init__()
            self.selection = selection
