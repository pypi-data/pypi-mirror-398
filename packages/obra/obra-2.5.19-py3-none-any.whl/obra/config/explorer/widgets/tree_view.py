"""Configuration Tree View widget.

Provides an interactive tree widget for browsing and editing configuration.
"""

from typing import Any

from textual.binding import Binding
from textual.message import Message
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from ..models import ConfigNode, ConfigTree, SettingTier, ValueType


class ConfigTreeView(Tree[ConfigNode]):
    """Interactive tree view of configuration.

    Extends Textual's Tree widget to display ConfigNode structures with
    proper formatting, expand/collapse, and selection handling.
    """

    # Vim-style navigation bindings (arrow keys are handled by parent Tree widget)
    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("h", "cursor_parent", "Collapse/Parent", show=False),
        Binding("l", "cursor_expand", "Expand/Enter", show=False),
        Binding("enter", "select_cursor", "Toggle/Edit", priority=True),
        Binding("space", "toggle_node", "Expand/Collapse", show=False),
    ]

    DEFAULT_CSS = """
    ConfigTreeView {
        height: 1fr;
        scrollbar-gutter: stable;
        padding: 1;
    }

    ConfigTreeView > .tree--cursor {
        background: $accent;
        color: $text;
    }

    ConfigTreeView > .tree--guides {
        color: $text-muted;
    }

    ConfigTreeView > .tree--guides-hover {
        color: $primary;
    }
    """

    def __init__(
        self,
        config_tree: ConfigTree,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the tree view.

        Args:
            config_tree: ConfigTree containing local and server configurations
            *args: Additional positional arguments for Tree
            **kwargs: Additional keyword arguments for Tree
        """
        super().__init__("Configuration", *args, **kwargs)
        self.config_tree = config_tree
        self._node_map: dict[str, TreeNode[ConfigNode]] = {}

    def on_mount(self) -> None:
        """Build the UI tree when mounted."""
        self._build_ui_tree()
        # Ensure root is expanded to show Local/Server sections
        self.root.expand()

    def _build_ui_tree(self) -> None:
        """Populate the Textual Tree from ConfigTree."""
        # Clear existing nodes
        self.root.remove_children()
        self._node_map.clear()

        # Local settings section
        local_label = self._format_section_label(
            self.config_tree.local_root.key,
            self.config_tree.local_root,
        )
        local_node = self.root.add(local_label, expand=True)
        local_node.data = self.config_tree.local_root
        self._add_config_children(local_node, self.config_tree.local_root)

        # Server settings section
        server_label = self._format_section_label(
            self.config_tree.server_root.key,
            self.config_tree.server_root,
        )
        server_node = self.root.add(server_label, expand=True)
        server_node.data = self.config_tree.server_root
        self._add_config_children(server_node, self.config_tree.server_root)

    def _format_section_label(self, label: str, node: ConfigNode) -> str:
        """Format a section header label with item count.

        Args:
            label: Base label text
            node: ConfigNode to count children of

        Returns:
            Formatted label like "Local Settings (5 items)"
        """
        count = self._count_leaf_children(node)
        if count > 0:
            return f"{label} ({count} items)"
        return label

    def _count_leaf_children(self, node: ConfigNode) -> int:
        """Count leaf nodes (actual settings) in a config node.

        Args:
            node: ConfigNode to count

        Returns:
            Number of leaf children
        """
        count = 0
        for child in node.children:
            if child.is_leaf:
                count += 1
            else:
                count += self._count_leaf_children(child)
        return count

    def _add_config_children(
        self,
        ui_node: TreeNode[ConfigNode],
        config_node: ConfigNode,
    ) -> None:
        """Recursively add ConfigNode children to UI tree.

        Args:
            ui_node: Textual TreeNode to add children to
            config_node: ConfigNode containing children to add
        """
        for child in config_node.children:
            if child.is_leaf:
                # Leaf node with value
                label = self._format_leaf(child)
                leaf = ui_node.add_leaf(label, data=child)
                self._node_map[child.path] = leaf
            else:
                # Branch node (expandable)
                # Collapse advanced sections by default
                should_expand = child.tier != SettingTier.ADVANCED
                tier_suffix = " (advanced)" if child.tier == SettingTier.ADVANCED else ""

                branch_label = f"{child.key}{tier_suffix}"
                branch = ui_node.add(branch_label, expand=should_expand, data=child)
                self._node_map[child.path] = branch
                self._add_config_children(branch, child)

    def _format_leaf(self, node: ConfigNode) -> str:
        """Format a leaf node for display.

        Args:
            node: ConfigNode to format

        Returns:
            Formatted label string
        """
        modified = " *" if node.is_modified else ""
        readonly_marker = " [dim](read-only)[/dim]" if node.is_readonly else ""

        if node.value_type == ValueType.BOOLEAN:
            icon = "●" if node.value else "○"
            value_str = str(node.value).lower()
            return f"{icon} {node.key}: {value_str}{modified}{readonly_marker}"

        value_str = str(node.value) if node.value is not None else "null"
        return f"{node.key}: {value_str}{modified}{readonly_marker}"

    def refresh_node(self, path: str) -> None:
        """Refresh the display of a specific node.

        Args:
            path: Dot-notation path of the node to refresh
        """
        if path not in self._node_map:
            return

        ui_node = self._node_map[path]
        config_node = self.config_tree.get_node(path)

        if config_node and config_node.is_leaf:
            ui_node.set_label(self._format_leaf(config_node))

    def refresh_tree(self) -> None:
        """Rebuild the entire tree from the config data.

        Use this after bulk changes to the config tree.
        """
        self._build_ui_tree()

    def get_selected_node(self) -> ConfigNode | None:
        """Get the ConfigNode for the currently selected tree node.

        Returns:
            The selected ConfigNode or None
        """
        if self.cursor_node is None:
            return None
        return self.cursor_node.data

    def find_node_by_path(self, path: str) -> TreeNode[ConfigNode] | None:
        """Find a tree node by its config path.

        Args:
            path: Dot-notation path

        Returns:
            The TreeNode or None if not found
        """
        return self._node_map.get(path)

    def expand_to_path(self, path: str) -> None:
        """Expand all parent nodes to reveal a path.

        Args:
            path: Dot-notation path to reveal
        """
        parts = path.split(".")
        current_path = ""

        for part in parts[:-1]:  # Don't include the final node
            current_path = f"{current_path}.{part}" if current_path else part
            node = self._node_map.get(current_path)
            if node and not node.is_expanded:
                node.expand()

    def scroll_to_path(self, path: str) -> None:
        """Scroll to make a path visible.

        Args:
            path: Dot-notation path to scroll to
        """
        self.expand_to_path(path)
        node = self._node_map.get(path)
        if node:
            self.select_node(node)
            self.scroll_to_node(node)

    def action_cursor_parent(self) -> None:
        """Move to parent node or collapse if expanded.

        Vim 'h' key behavior: if current node is expanded, collapse it.
        Otherwise, move to the parent node.
        """
        if self.cursor_node is None:
            return

        if self.cursor_node.is_expanded and self.cursor_node.children:
            # Collapse the current node
            self.cursor_node.collapse()
        elif self.cursor_node.parent is not None:
            # Move to parent
            self.select_node(self.cursor_node.parent)

    def action_cursor_expand(self) -> None:
        """Expand node or move to first child.

        Vim 'l' key behavior: if current node is collapsed, expand it.
        If already expanded, move to first child. If leaf, do nothing.
        """
        if self.cursor_node is None:
            return

        if not self.cursor_node.is_expanded and self.cursor_node.children:
            # Expand the current node
            self.cursor_node.expand()
        elif self.cursor_node.is_expanded and self.cursor_node.children:
            # Move to first child
            first_child = self.cursor_node.children[0]
            self.select_node(first_child)

    def action_select_cursor(self) -> None:
        """Handle Enter key on selected node.

        For boolean nodes: toggle the value.
        For string/enum nodes: emit event to open edit modal.
        For branch nodes: expand/collapse.
        Read-only nodes cannot be edited.
        """
        if self.cursor_node is None:
            return

        config_node = self.cursor_node.data
        if config_node is None:
            return

        # Block editing on read-only fields
        if config_node.is_readonly:
            self.app.notify("This field is read-only")
            return

        if config_node.value_type == ValueType.BOOLEAN:
            self._toggle_boolean(config_node)
        elif config_node.is_leaf:
            # String/enum/integer - emit event for edit modal
            self.post_message(self.EditRequested(config_node))
        # Branch node - toggle expand/collapse
        elif self.cursor_node.is_expanded:
            self.cursor_node.collapse()
        else:
            self.cursor_node.expand()

    def _toggle_boolean(self, node: ConfigNode) -> None:
        """Toggle a boolean config value.

        Args:
            node: ConfigNode with boolean value to toggle
        """
        new_value = not node.value
        success = self.config_tree.set_value(node.path, new_value)

        if success:
            # Refresh the display
            self.refresh_node(node.path)
            # Update status bar
            self.post_message(self.ValueChanged(node.path, new_value))

    class EditRequested(Message):
        """Message posted when a non-boolean node needs editing."""

        def __init__(self, node: ConfigNode) -> None:
            super().__init__()
            self.node = node

    class ValueChanged(Message):
        """Message posted when a config value has changed."""

        def __init__(self, path: str, value: Any) -> None:
            super().__init__()
            self.path = path
            self.value = value
