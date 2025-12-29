"""LLM Wizard modal for guided LLM configuration.

Provides a three-step wizard for changing LLM settings:
1. Select role (orchestrator, implementation, or both)
2. Select provider (anthropic, google, openai)
3. Select model (default, specific models)
"""

from dataclasses import dataclass
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Label, OptionList, Static
from textual.widgets.option_list import Option

# LLM provider definitions with descriptions
PROVIDERS = [
    ("anthropic", "Claude", "Best for complex reasoning"),
    ("google", "Gemini", "Fast, good for simple tasks"),
    ("openai", "GPT", "Alternative option"),
]

# Model definitions per provider
MODELS = {
    "anthropic": [
        ("default", "Let Obra choose"),
        ("sonnet", "Claude Sonnet - Fast, capable"),
        ("opus", "Claude Opus - Most capable, slower"),
        ("haiku", "Claude Haiku - Fastest, lighter tasks"),
    ],
    "google": [
        ("default", "Let Obra choose"),
        ("gemini-pro", "Gemini Pro - Standard"),
        ("gemini-1.5-flash", "Gemini Flash - Fastest"),
    ],
    "openai": [
        ("default", "Let Obra choose"),
        ("gpt-4", "GPT-4 - Most capable"),
        ("gpt-4-turbo", "GPT-4 Turbo - Faster"),
        ("gpt-3.5-turbo", "GPT-3.5 - Fastest, budget-friendly"),
    ],
}

# Role definitions
ROLES = [
    ("orchestrator", "Orchestrator", "Planning, validation, decisions"),
    ("implementation", "Implementation", "Code generation"),
    ("both", "Both", "Change both to same provider"),
]


@dataclass
class LLMSelection:
    """Result of LLM wizard selection."""

    role: str  # "orchestrator", "implementation", or "both"
    provider: str
    model: str


class LLMWizard(ModalScreen[Optional[LLMSelection]]):
    """Three-step wizard for configuring LLM settings.

    Steps:
    1. Select role (orchestrator/implementation/both)
    2. Select provider (anthropic/google/openai)
    3. Select model
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select", priority=True),
        Binding("backspace", "back", "Back", show=False),
    ]

    DEFAULT_CSS = """
    LLMWizard {
        align: center middle;
    }

    LLMWizard > Container {
        width: 70;
        height: auto;
        max-height: 25;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    LLMWizard #title {
        text-style: bold;
        width: 100%;
        text-align: center;
        margin-bottom: 1;
    }

    LLMWizard #step-indicator {
        color: $text-muted;
        text-align: center;
        margin-bottom: 1;
    }

    LLMWizard #description {
        color: $text-muted;
        margin-bottom: 1;
    }

    LLMWizard OptionList {
        height: auto;
        max-height: 12;
        margin-bottom: 1;
    }

    LLMWizard .buttons {
        height: 3;
        align: center middle;
    }

    LLMWizard Button {
        margin: 0 1;
    }

    LLMWizard #current-selection {
        color: $text-muted;
        margin-bottom: 1;
        padding: 0 1;
        background: $surface-darken-1;
    }
    """

    def __init__(
        self,
        current_orchestrator_provider: str = "anthropic",
        current_orchestrator_model: str = "default",
        current_implementation_provider: str = "anthropic",
        current_implementation_model: str = "default",
    ) -> None:
        """Initialize the LLM wizard.

        Args:
            current_orchestrator_provider: Current orchestrator provider
            current_orchestrator_model: Current orchestrator model
            current_implementation_provider: Current implementation provider
            current_implementation_model: Current implementation model
        """
        super().__init__()
        self._step = 1  # 1=role, 2=provider, 3=model
        self._role: str | None = None
        self._provider: str | None = None
        self._model: str | None = None

        # Store current values for display
        self._current = {
            "orchestrator": {
                "provider": current_orchestrator_provider,
                "model": current_orchestrator_model,
            },
            "implementation": {
                "provider": current_implementation_provider,
                "model": current_implementation_model,
            },
        }

    def compose(self) -> ComposeResult:
        """Create the wizard content."""
        with Container():
            yield Label("Change LLM Provider", id="title")
            yield Static("Step 1 of 3", id="step-indicator")
            yield Static("", id="current-selection")
            yield Static("Which role do you want to configure?", id="description")
            yield OptionList(id="options")
            with Horizontal(classes="buttons"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Back", variant="default", id="back", disabled=True)
                yield Button("Next", variant="primary", id="next")

    def on_mount(self) -> None:
        """Initialize the first step."""
        self._update_step()

    def _update_step(self) -> None:
        """Update the wizard display for the current step."""
        title = self.query_one("#title", Label)
        step_indicator = self.query_one("#step-indicator", Static)
        description = self.query_one("#description", Static)
        current_selection = self.query_one("#current-selection", Static)
        option_list = self.query_one("#options", OptionList)
        back_btn = self.query_one("#back", Button)
        next_btn = self.query_one("#next", Button)

        # Clear existing options
        option_list.clear_options()

        # Update based on step
        if self._step == 1:
            title.update("Change LLM Provider")
            step_indicator.update("Step 1 of 3")
            description.update("Which role do you want to configure?")
            current_selection.update("")
            back_btn.disabled = True
            next_btn.label = "Next"

            # Add role options with current values
            for role_id, role_name, role_desc in ROLES:
                if role_id == "both":
                    label = f"{role_name} - {role_desc}"
                else:
                    current = self._current.get(role_id, {})
                    current_prov = current.get("provider", "anthropic")
                    label = f"{role_name} - {role_desc} (current: {current_prov})"
                option_list.add_option(Option(label, id=role_id))

        elif self._step == 2:
            title.update("Select Provider")
            step_indicator.update("Step 2 of 3")
            description.update("Choose an LLM provider:")

            # Show what we've selected
            role_display = (
                "Both" if self._role == "both" else (self._role or "").capitalize()
            )
            current_selection.update(f"Role: {role_display}")

            back_btn.disabled = False
            next_btn.label = "Next"

            # Add provider options
            for prov_id, prov_name, prov_desc in PROVIDERS:
                label = f"{prov_name} - {prov_desc}"
                option_list.add_option(Option(label, id=prov_id))

        elif self._step == 3:
            title.update("Select Model")
            step_indicator.update("Step 3 of 3")
            description.update("Choose a model:")

            # Show what we've selected
            role_display = (
                "Both" if self._role == "both" else (self._role or "").capitalize()
            )
            prov_display = (self._provider or "").capitalize()
            current_selection.update(f"Role: {role_display} | Provider: {prov_display}")

            back_btn.disabled = False
            next_btn.label = "Apply"

            # Add model options for selected provider
            models = MODELS.get(self._provider or "anthropic", MODELS["anthropic"])
            for model_id, model_desc in models:
                option_list.add_option(Option(model_desc, id=model_id))

        # Focus the option list and highlight first option
        option_list.focus()
        if option_list.option_count > 0:
            option_list.highlighted = 0

    def action_cancel(self) -> None:
        """Cancel the wizard."""
        self.dismiss(None)

    def action_back(self) -> None:
        """Go back to previous step."""
        if self._step > 1:
            self._step -= 1
            if self._step == 1:
                self._role = None
            elif self._step == 2:
                self._provider = None
            self._update_step()

    def action_select(self) -> None:
        """Select current option and advance."""
        self._advance_step()

    def _advance_step(self) -> None:
        """Advance to the next step or finish."""
        option_list = self.query_one("#options", OptionList)

        if option_list.highlighted is None:
            return

        # Get selected option ID
        selected_option = option_list.get_option_at_index(option_list.highlighted)
        selected_id = str(selected_option.id) if selected_option else None

        if not selected_id:
            return

        if self._step == 1:
            self._role = selected_id
            self._step = 2
            self._update_step()
        elif self._step == 2:
            self._provider = selected_id
            self._step = 3
            self._update_step()
        elif self._step == 3:
            self._model = selected_id
            # Complete the wizard
            if self._role and self._provider and self._model:
                self.dismiss(
                    LLMSelection(
                        role=self._role,
                        provider=self._provider,
                        model=self._model,
                    )
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "cancel":
            self.action_cancel()
        elif event.button.id == "back":
            self.action_back()
        elif event.button.id == "next":
            self._advance_step()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option double-click/enter."""
        self._advance_step()

    class LLMChanged(Message):
        """Message posted when LLM configuration is changed."""

        def __init__(self, selection: LLMSelection) -> None:
            super().__init__()
            self.selection = selection
