"""Configuration Explorer Textual Application.

Main application class for the interactive configuration browser.
"""

from importlib.resources import files
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Footer, Header, Static, Tree

from obra import config

from .models import ConfigTree
from .utils import dict_to_config_tree, find_nodes_by_path_pattern, get_preset_name
from .widgets import (
    ConfigTreeView,
    EditModal,
    HelpOverlay,
    LLMSelection,
    LLMWizard,
    PresetPicker,
    PresetSelection,
    QuickActionsBar,
    SearchBar,
    UnsavedAction,
    UnsavedChangesModal,
)


class OfflineBanner(Static):
    """Warning banner shown when server connection is unavailable."""

    DEFAULT_CSS = """
    OfflineBanner {
        height: auto;
        padding: 0 1;
        background: $warning-darken-3;
        color: $warning;
        text-style: bold;
    }
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.update(
            "Offline Mode - Server unavailable. "
            "Local settings are editable, server settings are read-only."
        )


class DescriptionPanel(Static):
    """Panel showing the description of the currently selected setting."""

    DEFAULT_CSS = """
    DescriptionPanel {
        height: auto;
        min-height: 3;
        max-height: 6;
        padding: 0 1;
        background: $surface;
        border-top: solid $primary;
    }
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._description = "Select a setting to see its description."

    def update_description(self, description: str | None, path: str = "") -> None:
        """Update the displayed description.

        Args:
            description: Description text to show
            path: Path of the setting being described
        """
        if description:
            self._description = f"[bold]{path}[/bold]\n{description}"
        else:
            self._description = f"[bold]{path}[/bold]\nNo description available."
        self.update(self._description)


class StatusBar(Static):
    """Status bar showing pending changes, preset, and connection status."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        dock: bottom;
        padding: 0 1;
        background: $primary-background;
        color: $text;
    }
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._pending_count = 0
        self._preset = "unknown"
        self._connected = True

    def update_status(
        self,
        pending_count: int = 0,
        preset: str = "unknown",
        connected: bool = True,
    ) -> None:
        """Update the status bar content.

        Args:
            pending_count: Number of pending changes
            preset: Current preset name
            connected: Whether server connection is active
        """
        self._pending_count = pending_count
        self._preset = preset
        self._connected = connected

        changes_text = f"{pending_count} unsaved change{'s' if pending_count != 1 else ''}"
        if pending_count == 0:
            changes_text = "No unsaved changes"

        connection_icon = "[green]o[/green]" if connected else "[red]x[/red]"
        connection_text = "Connected" if connected else "Offline"

        self.update(
            f"{changes_text} | preset: {preset} | {connection_icon} {connection_text}"
        )


class ConfigExplorerApp(App):
    """Interactive TUI for browsing and editing Obra configuration.

    Features:
    - Tree-based navigation of configuration
    - Inline editing of values
    - Quick action wizards for common operations
    - Staged changes with explicit save
    """

    TITLE = "Obra Configuration Explorer"

    # Use importlib.resources to access package data file (works in installed packages)
    CSS_PATH = str(files("obra.config.explorer.styles").joinpath("explorer.tcss"))

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("s", "save", "Save"),
        Binding("r", "refresh", "Refresh"),
        Binding("R", "reset", "Reset"),
        Binding("slash", "search", "Search"),
        Binding("question_mark", "help", "Help"),
        Binding("1", "quick_llm", "Change LLM"),
        Binding("2", "quick_preset", "Preset"),
        Binding("p", "quick_preset", "Preset", show=False),
        Binding("3", "quick_features", "Features"),
    ]

    def __init__(
        self,
        local_config: dict[str, Any] | None = None,
        server_config: dict[str, Any] | None = None,
        initial_section: str | None = None,
        api_client: Any | None = None,
    ) -> None:
        """Initialize the Configuration Explorer.

        Args:
            local_config: Local configuration dictionary
            server_config: Server configuration dictionary
            initial_section: Section to expand initially (llm, features, advanced)
            api_client: API client for server operations
        """
        super().__init__()
        self._local_config = local_config or {}
        self._server_config = server_config or {}
        self._initial_section = initial_section
        self._api_client = api_client
        self._config_tree: ConfigTree | None = None
        # Assume disconnected if no API client or no server config
        self._connected = api_client is not None and bool(server_config)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        # Show offline banner if not connected
        if not self._connected:
            yield OfflineBanner(id="offline-banner")
        yield QuickActionsBar(id="quick-actions")
        yield SearchBar(id="search")
        yield Container(
            Vertical(
                # Tree will be added after config_tree is built in on_mount
                id="tree-container",
            ),
            DescriptionPanel(id="description"),
            id="main",
        )
        yield StatusBar(id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        # Build the config tree
        self._config_tree = dict_to_config_tree(
            self._local_config,
            self._server_config,
        )

        # Add the tree view to the container
        tree_container = self.query_one("#tree-container", Vertical)
        tree_view = ConfigTreeView(self._config_tree, id="tree")
        tree_container.mount(tree_view)

        # Update status bar with preset info
        preset = get_preset_name(self._server_config) or "default"
        status_bar = self.query_one("#status", StatusBar)
        status_bar.update_status(
            pending_count=0,
            preset=preset,
            connected=self._connected,
        )

        # Expand and scroll to initial section if specified
        if self._initial_section:
            section_mappings = {
                "llm": "llm",
                "features": "features",
                "advanced": "advanced",
            }
            target_path = section_mappings.get(self._initial_section)
            if target_path:
                # Schedule the scroll after the tree is fully mounted
                self.call_after_refresh(lambda: tree_view.scroll_to_path(target_path))

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Update description panel when tree selection changes."""
        node_data = event.node.data
        description_panel = self.query_one("#description", DescriptionPanel)

        if node_data is not None:
            description_panel.update_description(
                node_data.description,
                node_data.path or node_data.key,
            )
        else:
            description_panel.update_description(None, "")

    def on_config_tree_view_value_changed(
        self, event: ConfigTreeView.ValueChanged
    ) -> None:
        """Update status bar when a config value changes."""
        self._update_status_bar()

    def on_config_tree_view_edit_requested(
        self, event: ConfigTreeView.EditRequested
    ) -> None:
        """Open edit modal when a non-boolean node is selected."""
        self._open_edit_modal(event.node)

    def _open_edit_modal(self, node: Any) -> None:
        """Open the edit modal for a config node.

        Args:
            node: ConfigNode to edit
        """
        from .models import ConfigNode

        if not isinstance(node, ConfigNode):
            return

        def handle_result(result: Any) -> None:
            if result is not None and self._config_tree is not None:
                # Apply the change
                self._config_tree.set_value(node.path, result)
                # Refresh the tree display
                tree_view = self.query_one("#tree", ConfigTreeView)
                tree_view.refresh_node(node.path)
                # Update status bar
                self._update_status_bar()

        self.push_screen(EditModal(node, self._config_tree), handle_result)

    def _update_status_bar(self) -> None:
        """Update the status bar with current pending changes count."""
        if self._config_tree is None:
            return

        status_bar = self.query_one("#status", StatusBar)
        preset = get_preset_name(self._server_config) or "default"
        status_bar.update_status(
            pending_count=self._config_tree.pending_count,
            preset=preset,
            connected=self._connected,
        )

    def action_quit(self) -> None:
        """Quit the application, checking for unsaved changes."""
        if self._config_tree and self._config_tree.has_pending_changes:
            # Show unsaved changes modal
            self._show_unsaved_changes_modal()
        else:
            self.exit()

    def _show_unsaved_changes_modal(self) -> None:
        """Show the unsaved changes modal and handle the result."""
        pending_count = self._config_tree.pending_count if self._config_tree else 0

        def handle_result(action: UnsavedAction | None) -> None:
            if action == UnsavedAction.SAVE:
                # Save changes then quit
                self.action_save()
                # Check if save succeeded (no more pending changes)
                if self._config_tree and not self._config_tree.has_pending_changes:
                    self.exit()
                # If save failed, stay in app (errors already notified)
            elif action == UnsavedAction.DISCARD:
                # Discard changes and quit
                if self._config_tree:
                    self._config_tree.discard_changes()
                self.exit()
            # CANCEL: do nothing, stay in app

        self.push_screen(UnsavedChangesModal(pending_count), handle_result)

    def action_save(self) -> None:
        """Save pending changes to local config and/or server."""
        if not self._config_tree or not self._config_tree.has_pending_changes:
            self.notify("No changes to save")
            return

        # Get local and server changes separately
        local_changes = self._config_tree.get_local_changes()
        server_changes = self._config_tree.get_server_changes()

        saved_count = 0
        errors: list[str] = []

        # Save local changes
        if local_changes:
            try:
                self._save_local_changes(local_changes)
                saved_count += len(local_changes)
            except Exception as e:
                errors.append(f"Local save failed: {e}")

        # Save server changes
        if server_changes:
            try:
                self._save_server_changes(server_changes)
                saved_count += len(server_changes)
            except Exception as e:
                errors.append(f"Server save failed: {e}")

        # Clear pending changes on success
        if not errors:
            self._config_tree.clear_pending()
            self._update_status_bar()
            self.notify(f"Saved {saved_count} change{'s' if saved_count != 1 else ''}")
        else:
            # Partial save - report errors
            error_msg = "; ".join(errors)
            self.notify(f"Save errors: {error_msg}", severity="error")

    def _save_local_changes(self, changes: dict[str, Any]) -> None:
        """Save local config changes to ~/.obra/client-config.yaml.

        Args:
            changes: Dictionary of path -> new_value pairs

        Raises:
            Exception: If save fails
        """
        # Load current config
        current_config = config.load_config()

        # Apply changes (paths are dot-notation like "llm.orchestrator.provider")
        for path, value in changes.items():
            self._set_nested_value(current_config, path, value)

        # Save updated config
        config.save_config(current_config)

        # Update our local copy
        self._local_config = current_config

    def _set_nested_value(self, d: dict[str, Any], path: str, value: Any) -> None:
        """Set a value in a nested dictionary using dot-notation path.

        Args:
            d: Dictionary to modify
            path: Dot-notation path like "llm.orchestrator.provider"
            value: Value to set
        """
        parts = path.split(".")
        current = d

        # Navigate/create nested structure
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Set the final value
        current[parts[-1]] = value

    def _save_server_changes(self, changes: dict[str, Any]) -> None:
        """Save server config changes via API client.

        Args:
            changes: Dictionary of path -> new_value pairs

        Raises:
            RuntimeError: If no API client configured
            Exception: If API call fails
        """
        if self._api_client is None:
            raise RuntimeError(
                "No API client configured - cannot save server changes. "
                "You may be in offline mode."
            )

        if not self._connected:
            raise RuntimeError(
                "Server connection unavailable. "
                "Please check your network and try again."
            )

        # Convert changes to overrides format for API
        overrides = {}
        for path, value in changes.items():
            # Strip any "Server Settings (SaaS)." prefix if present
            clean_path = path
            for prefix in ["Server Settings (SaaS).", "resolved."]:
                if clean_path.startswith(prefix):
                    clean_path = clean_path[len(prefix):]
            overrides[clean_path] = value

        try:
            # Call API to update config
            result = self._api_client.update_user_config(overrides=overrides)

            # Update our server config copy
            self._server_config = result
        except Exception as e:
            # Mark as disconnected on API failure
            self._set_offline_mode()
            raise RuntimeError(f"Server save failed: {e}") from e

    def _set_offline_mode(self) -> None:
        """Switch to offline mode when server becomes unavailable."""
        if self._connected:
            self._connected = False
            self._update_status_bar()
            # Add offline banner if not already present
            try:
                self.query_one("#offline-banner", OfflineBanner)
            except Exception:
                # Banner not present, add it after header
                header = self.query_one(Header)
                self.mount(OfflineBanner(id="offline-banner"), after=header)

    def action_refresh(self) -> None:
        """Refresh configuration from server (and local config)."""
        # Always refresh local config
        self._local_config = config.load_config()

        # Try to refresh server config if we have an API client
        if self._api_client is not None:
            try:
                server_config = self._api_client.get_user_config()
                self._server_config = server_config

                # Successfully connected - mark as online
                if not self._connected:
                    self._connected = True
                    # Remove offline banner if present
                    try:
                        banner = self.query_one("#offline-banner", OfflineBanner)
                        banner.remove()
                    except Exception:
                        pass
            except Exception as e:
                # Server unavailable - switch to offline mode
                self._set_offline_mode()
                self.notify(f"Server refresh failed: {e}", severity="warning")

        # Rebuild the config tree with fresh data
        self._config_tree = dict_to_config_tree(
            self._local_config,
            self._server_config,
        )

        # Refresh the tree view
        tree_container = self.query_one("#tree-container", Vertical)
        # Remove old tree
        old_tree = self.query_one("#tree", ConfigTreeView)
        old_tree.remove()
        # Add new tree
        tree_view = ConfigTreeView(self._config_tree, id="tree")
        tree_container.mount(tree_view)

        # Update status bar
        self._update_status_bar()

        self.notify("Configuration refreshed")

    def action_reset(self) -> None:
        """Reset selected item to its default value."""
        if not self._config_tree:
            return

        # Get the currently selected node
        tree_view = self.query_one("#tree", ConfigTreeView)
        selected_node = tree_view.get_selected_node()

        if selected_node is None:
            self.notify("No item selected")
            return

        if not selected_node.is_leaf:
            self.notify("Can only reset leaf settings, not sections")
            return

        if selected_node.default_value is None:
            self.notify("No default value available for this setting")
            return

        if selected_node.value == selected_node.default_value:
            self.notify("Already at default value")
            return

        # Reset to default
        self._config_tree.set_value(selected_node.path, selected_node.default_value)

        # Refresh the display
        tree_view.refresh_node(selected_node.path)
        self._update_status_bar()

        self.notify(f"Reset {selected_node.key} to default: {selected_node.default_value}")

    def action_search(self) -> None:
        """Enter search/filter mode."""
        search_bar = self.query_one("#search", SearchBar)
        search_bar.activate()

    def on_search_bar_search_applied(self, event: SearchBar.SearchApplied) -> None:
        """Handle search submission."""
        self._apply_search_filter(event.query)

    def on_search_bar_search_changed(self, event: SearchBar.SearchChanged) -> None:
        """Handle live search filtering as user types."""
        self._apply_search_filter(event.query)

    def on_search_bar_search_cleared(self, event: SearchBar.SearchCleared) -> None:
        """Handle search cancellation - show all nodes."""
        self._clear_search_filter()
        # Re-focus tree
        try:
            tree_view = self.query_one("#tree", ConfigTreeView)
            tree_view.focus()
        except Exception:
            pass

    def on_quick_actions_bar_action_clicked(
        self, event: QuickActionsBar.ActionClicked
    ) -> None:
        """Handle quick action button clicks."""
        if event.action == "llm":
            self.action_quick_llm()
        elif event.action == "preset":
            self.action_quick_preset()
        elif event.action == "features":
            self.action_quick_features()

    def _apply_search_filter(self, query: str) -> None:
        """Apply search filter to the tree.

        Args:
            query: Search query to filter by
        """
        if not self._config_tree or not query:
            return

        # Find matching nodes in both local and server trees
        local_matches = find_nodes_by_path_pattern(
            self._config_tree.local_root, query
        )
        server_matches = find_nodes_by_path_pattern(
            self._config_tree.server_root, query
        )

        all_matches = local_matches + server_matches

        if all_matches:
            # Expand and scroll to first match
            tree_view = self.query_one("#tree", ConfigTreeView)
            first_match = all_matches[0]
            if first_match.path:
                tree_view.scroll_to_path(first_match.path)

            self.notify(f"Found {len(all_matches)} matching settings")
        else:
            self.notify("No matching settings found", severity="warning")

    def _clear_search_filter(self) -> None:
        """Clear search filter and restore normal view."""
        # For now, just rebuild the tree to show all nodes
        # A more sophisticated implementation would track hidden nodes

    def action_help(self) -> None:
        """Show help overlay with all keybindings."""
        self.push_screen(HelpOverlay())

    def action_quick_llm(self) -> None:
        """Launch LLM change wizard."""
        # Get current LLM settings from local config
        llm_config = self._local_config.get("llm", {})
        orchestrator = llm_config.get("orchestrator", {})
        implementation = llm_config.get("implementation", {})

        wizard = LLMWizard(
            current_orchestrator_provider=orchestrator.get("provider", "anthropic"),
            current_orchestrator_model=orchestrator.get("model", "default"),
            current_implementation_provider=implementation.get("provider", "anthropic"),
            current_implementation_model=implementation.get("model", "default"),
        )

        def handle_result(result: LLMSelection | None) -> None:
            if result is None:
                return  # User cancelled

            # Apply the changes to config tree
            if self._config_tree is None:
                return

            roles = (
                ["orchestrator", "implementation"]
                if result.role == "both"
                else [result.role]
            )

            for role in roles:
                provider_path = f"llm.{role}.provider"
                model_path = f"llm.{role}.model"

                # Set provider and model
                self._config_tree.set_value(provider_path, result.provider)
                self._config_tree.set_value(model_path, result.model)

            # Refresh the tree display
            tree_view = self.query_one("#tree", ConfigTreeView)
            tree_view.refresh_tree()

            # Update status bar
            self._update_status_bar()

            role_text = "orchestrator and implementation" if result.role == "both" else result.role
            self.notify(
                f"LLM changed: {role_text} -> {result.provider}/{result.model}",
                severity="information",
            )

        self.push_screen(wizard, handle_result)

    def action_quick_preset(self) -> None:
        """Launch preset picker."""
        current_preset = get_preset_name(self._server_config) or "beta-tester-default"

        picker = PresetPicker(current_preset=current_preset)

        def handle_result(result: PresetSelection | None) -> None:
            if result is None:
                return  # User cancelled

            # Apply preset features to config tree
            if self._config_tree is None:
                return

            # Apply each feature toggle
            for feature_path, enabled in result.features.items():
                # Prefix with server config path
                full_path = f"features.{feature_path}"
                self._config_tree.set_value(full_path, enabled)

            # Refresh the tree display
            tree_view = self.query_one("#tree", ConfigTreeView)
            tree_view.refresh_tree()

            # Update status bar
            self._update_status_bar()

            self.notify(
                f"Preset applied: {result.preset_name}",
                severity="information",
            )

        self.push_screen(picker, handle_result)

    def action_quick_features(self) -> None:
        """Jump to features section in the tree."""
        tree_view = self.query_one("#tree", ConfigTreeView)

        # Try to find the features section - could be under server config
        # Look for nodes with "features" in their path
        features_paths = [
            "features",
            "resolved.features",
            "Server Settings (SaaS).resolved.features",
            "Server Settings (SaaS).features",
        ]

        for path in features_paths:
            node = tree_view.find_node_by_path(path)
            if node is not None:
                # Expand and scroll to this node
                tree_view.scroll_to_path(path)
                self.notify("Jumped to Features section")
                return

        # Fallback: try to find any node with "features" in it
        if self._config_tree is not None:
            matches = find_nodes_by_path_pattern(
                self._config_tree.server_root, "features"
            )
            if matches:
                first_match = matches[0]
                if first_match.path:
                    tree_view.scroll_to_path(first_match.path)
                    self.notify("Jumped to Features section")
                    return

        self.notify("Features section not found", severity="warning")


def run_explorer(
    local_config: dict[str, Any] | None = None,
    server_config: dict[str, Any] | None = None,
    initial_section: str | None = None,
    api_client: Any | None = None,
) -> None:
    """Run the Configuration Explorer application.

    Args:
        local_config: Local configuration dictionary
        server_config: Server configuration dictionary
        initial_section: Section to expand initially
        api_client: API client for server operations
    """
    app = ConfigExplorerApp(
        local_config=local_config,
        server_config=server_config,
        initial_section=initial_section,
        api_client=api_client,
    )
    app.run()


if __name__ == "__main__":
    # Allow running directly for testing
    run_explorer(
        local_config={
            "llm": {
                "orchestrator": {"provider": "anthropic", "model": "default"},
            }
        },
        server_config={
            "preset": "beta-tester",
            "resolved": {
                "features": {"budgets": {"enabled": True}},
            },
        },
    )
