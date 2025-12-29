"""Data models for Configuration Explorer.

Provides the core data structures for representing configuration as a tree
with typed values, change tracking, and metadata for descriptions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ConfigSource(Enum):
    """Where a configuration value originates."""

    LOCAL = "local"  # ~/.obra/client-config.yaml
    SERVER = "server"  # SaaS config (Firestore)
    DEFAULT = "default"  # Built-in default


class ValueType(Enum):
    """Type of a configuration value."""

    BOOLEAN = "boolean"
    STRING = "string"
    INTEGER = "integer"
    ENUM = "enum"  # String with predefined choices
    OBJECT = "object"  # Nested dict (expandable node)


class SettingTier(Enum):
    """Visibility tier for settings - controls initial UI state."""

    BASIC = "basic"  # Show by default, most users need
    STANDARD = "standard"  # Show by default, common use
    ADVANCED = "advanced"  # Collapsed by default, expert users


@dataclass
class ConfigNode:
    """Single node in the configuration tree.

    Represents either a leaf value (boolean, string, etc.) or a branch
    (object with children). Tracks modification state for staged changes.
    """

    key: str
    path: str  # Full dot-notation path (e.g., "llm.orchestrator.provider")
    value: Any
    value_type: ValueType
    source: ConfigSource
    tier: SettingTier = SettingTier.STANDARD
    description: str | None = None
    default_value: Any = None
    choices: list[str] | None = None  # For enum types
    depends_on: str | None = None  # Path of setting this depends on
    affects: list[str] = field(default_factory=list)  # Paths this setting affects
    children: list["ConfigNode"] = field(default_factory=list)
    is_modified: bool = False  # Changed from default/server
    is_expanded: bool = True  # UI state
    is_readonly: bool = False  # Read-only fields cannot be edited

    @property
    def is_leaf(self) -> bool:
        """Return True if this node has no children (is a value node)."""
        return self.value_type != ValueType.OBJECT

    @property
    def display_value(self) -> str:
        """Return formatted value for display in tree.

        Booleans show as filled/empty circles for quick visual scanning.
        """
        if self.value_type == ValueType.BOOLEAN:
            return "●" if self.value else "○"
        if self.value is None:
            return "null"
        return str(self.value)

    def get_child(self, key: str) -> Optional["ConfigNode"]:
        """Find a direct child by key name.

        Args:
            key: The key to search for

        Returns:
            The child ConfigNode or None if not found
        """
        for child in self.children:
            if child.key == key:
                return child
        return None


@dataclass
class ConfigTree:
    """Root container for both local and server configurations.

    Manages two separate configuration trees (local and server) and tracks
    pending changes until they are explicitly saved or discarded.
    """

    local_root: ConfigNode
    server_root: ConfigNode
    pending_changes: dict[str, tuple[Any, Any]] = field(default_factory=dict)
    # Maps path -> (old_value, new_value)

    def get_node(self, path: str) -> ConfigNode | None:
        """Traverse tree to find node by dot-notation path.

        Args:
            path: Dot-notation path like "llm.orchestrator.provider"

        Returns:
            The ConfigNode at that path, or None if not found
        """
        # Try local tree first
        node = self._find_in_tree(self.local_root, path)
        if node is not None:
            return node

        # Fall back to server tree
        return self._find_in_tree(self.server_root, path)

    def _find_in_tree(self, root: ConfigNode, path: str) -> ConfigNode | None:
        """Find a node in a specific tree by path.

        Args:
            root: Root node to search from
            path: Dot-notation path

        Returns:
            The ConfigNode or None
        """
        parts = path.split(".")
        current = root

        for part in parts:
            found = current.get_child(part)
            if found is None:
                return None
            current = found

        return current

    def set_value(self, path: str, value: Any) -> bool:
        """Stage a value change (doesn't persist until commit).

        Args:
            path: Dot-notation path to the setting
            value: New value to set

        Returns:
            True if the value was staged successfully
        """
        node = self.get_node(path)
        if node is None:
            return False

        # Track the change
        if path not in self.pending_changes:
            self.pending_changes[path] = (node.value, value)
        else:
            # Update the new value, keeping original old value
            old_value = self.pending_changes[path][0]
            self.pending_changes[path] = (old_value, value)

        # Update node state
        node.value = value
        node.is_modified = True

        return True

    def commit_changes(self) -> dict[str, Any]:
        """Return changes dict for API/file submission.

        Returns:
            Dictionary mapping paths to their new values
        """
        return {path: new_val for path, (_, new_val) in self.pending_changes.items()}

    def get_local_changes(self) -> dict[str, Any]:
        """Get only changes that apply to local config.

        Returns:
            Dictionary of local config changes
        """
        changes = {}
        for path, (_, new_val) in self.pending_changes.items():
            node = self.get_node(path)
            if node and node.source == ConfigSource.LOCAL:
                changes[path] = new_val
        return changes

    def get_server_changes(self) -> dict[str, Any]:
        """Get only changes that apply to server config.

        Returns:
            Dictionary of server config changes
        """
        changes = {}
        for path, (_, new_val) in self.pending_changes.items():
            node = self.get_node(path)
            if node and node.source == ConfigSource.SERVER:
                changes[path] = new_val
        return changes

    def discard_changes(self) -> None:
        """Revert all pending changes to their original values."""
        for path, (old_val, _) in self.pending_changes.items():
            node = self.get_node(path)
            if node:
                node.value = old_val
                node.is_modified = False

        self.pending_changes.clear()

    def clear_pending(self) -> None:
        """Clear pending changes without reverting values.

        Use after successful save to mark all changes as committed.
        """
        for path in self.pending_changes:
            node = self.get_node(path)
            if node:
                node.is_modified = False

        self.pending_changes.clear()

    @property
    def has_pending_changes(self) -> bool:
        """Check if there are any unsaved changes."""
        return len(self.pending_changes) > 0

    @property
    def pending_count(self) -> int:
        """Return the number of pending changes."""
        return len(self.pending_changes)
