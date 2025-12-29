"""Utility functions for the Configuration Explorer.

Provides functions for converting raw config dictionaries into ConfigTree
structures and other helper utilities.
"""

from typing import Any

from .descriptions import get_choices, get_default, get_description, get_tier
from .models import ConfigNode, ConfigSource, ConfigTree, SettingTier, ValueType

# Fields that should never appear in the explorer (security-sensitive)
HIDDEN_FIELDS = {
    "auth_token",
    "refresh_token",
    "firebase_api_key",
    "token_expires_at",
}

# Fields that should be displayed but not editable
READONLY_FIELDS = {
    "user_email",
    "firebase_uid",
    "auth_provider",
    "display_name",
    "user_id",
}

# Field ordering priority within the same tier (lower = earlier)
# Used to ensure parent fields appear before dependent fields
FIELD_ORDER_PRIORITY = {
    "provider": 0,  # Provider must come before model (parent → child)
    "model": 1,
    "auth_method": 2,
}


def detect_value_type(value: Any, path: str) -> ValueType:
    """Detect the ValueType for a configuration value.

    Args:
        value: The value to inspect
        path: The dot-notation path (used to check for known enum types)

    Returns:
        The detected ValueType
    """
    # Check if this path has predefined choices (enum)
    if get_choices(path) is not None:
        return ValueType.ENUM

    if isinstance(value, bool):
        return ValueType.BOOLEAN
    if isinstance(value, int):
        return ValueType.INTEGER
    if isinstance(value, str):
        return ValueType.STRING
    if isinstance(value, dict):
        return ValueType.OBJECT

    # Default to string for unknown types
    return ValueType.STRING


def get_setting_tier(path: str) -> SettingTier:
    """Get the SettingTier for a configuration path.

    Args:
        path: Dot-notation path

    Returns:
        The SettingTier for this setting
    """
    tier_str = get_tier(path)
    return SettingTier(tier_str)


def dict_to_config_node(
    data: dict[str, Any],
    source: ConfigSource,
    parent_path: str = "",
) -> ConfigNode:
    """Convert a dictionary into a ConfigNode tree.

    Recursively builds a ConfigNode tree from a nested dictionary,
    attaching descriptions, choices, and defaults from the registry.

    Args:
        data: Dictionary of configuration values
        source: ConfigSource indicating where this config comes from
        parent_path: Parent path for building full dot-notation paths

    Returns:
        Root ConfigNode containing the tree structure
    """
    # Create root node for this level
    key = parent_path.split(".")[-1] if parent_path else "root"
    root = ConfigNode(
        key=key,
        path=parent_path,
        value=None,
        value_type=ValueType.OBJECT,
        source=source,
        tier=get_setting_tier(parent_path) if parent_path else SettingTier.STANDARD,
        description=get_description(parent_path) if parent_path else None,
    )

    for k, v in data.items():
        # Skip sensitive fields that shouldn't be visible
        if k in HIDDEN_FIELDS:
            continue

        child_path = f"{parent_path}.{k}" if parent_path else k

        if isinstance(v, dict):
            # Recursive case - nested object
            child = dict_to_config_node(v, source, child_path)
            child.key = k
        else:
            # Leaf case - actual value
            value_type = detect_value_type(v, child_path)
            child = ConfigNode(
                key=k,
                path=child_path,
                value=v,
                value_type=value_type,
                source=source,
                tier=get_setting_tier(child_path),
                description=get_description(child_path),
                default_value=get_default(child_path),
                choices=get_choices(child_path),
                is_readonly=k in READONLY_FIELDS,
            )

        root.children.append(child)

    # Sort children: basic first, then standard, then advanced
    # Within same tier, sort by field priority (provider before model), then alphabetically
    tier_order = {SettingTier.BASIC: 0, SettingTier.STANDARD: 1, SettingTier.ADVANCED: 2}
    root.children.sort(
        key=lambda n: (
            tier_order.get(n.tier, 1),
            FIELD_ORDER_PRIORITY.get(n.key, 999),  # Fields with priority come first
            n.key,  # Alphabetical within same tier/priority
        )
    )

    return root


def dict_to_config_tree(
    local_config: dict[str, Any],
    server_config: dict[str, Any],
) -> ConfigTree:
    """Convert local and server config dicts into a ConfigTree.

    Args:
        local_config: Local configuration dictionary from ~/.obra/client-config.yaml
        server_config: Server configuration dictionary from API

    Returns:
        ConfigTree with both local and server roots populated
    """
    # Handle server config structure (may have resolved/overrides/preset keys)
    server_data = server_config.get("resolved", server_config)

    local_root = dict_to_config_node(local_config, ConfigSource.LOCAL, "")
    local_root.key = "Local Settings"

    server_root = dict_to_config_node(server_data, ConfigSource.SERVER, "")
    server_root.key = "Server Settings (SaaS)"

    return ConfigTree(local_root=local_root, server_root=server_root)


def flatten_config(node: ConfigNode, prefix: str = "") -> dict[str, Any]:
    """Flatten a ConfigNode tree into a dot-notation dictionary.

    Args:
        node: ConfigNode to flatten
        prefix: Current path prefix

    Returns:
        Dictionary mapping dot-notation paths to values
    """
    result: dict[str, Any] = {}

    for child in node.children:
        path = f"{prefix}.{child.key}" if prefix else child.key

        if child.is_leaf:
            result[path] = child.value
        else:
            result.update(flatten_config(child, path))

    return result


def unflatten_config(flat_config: dict[str, Any]) -> dict[str, Any]:
    """Convert a flat dot-notation dict back to nested structure.

    Args:
        flat_config: Dictionary with dot-notation keys

    Returns:
        Nested dictionary structure
    """
    result: dict[str, Any] = {}

    for path, value in flat_config.items():
        parts = path.split(".")
        current = result

        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return result


def get_preset_name(server_config: dict[str, Any]) -> str | None:
    """Extract preset name from server config.

    Args:
        server_config: Server configuration dictionary

    Returns:
        Preset name or None
    """
    return server_config.get("preset")


def count_children(node: ConfigNode, include_nested: bool = True) -> int:
    """Count child nodes in a config tree.

    Args:
        node: ConfigNode to count children of
        include_nested: If True, count recursively; if False, count direct children only

    Returns:
        Number of child nodes
    """
    if not include_nested:
        return len(node.children)

    count = 0
    for child in node.children:
        if child.is_leaf:
            count += 1
        else:
            count += count_children(child, include_nested=True)

    return count


def find_nodes_by_path_pattern(
    root: ConfigNode,
    pattern: str,
) -> list[ConfigNode]:
    """Find all nodes whose paths match a pattern.

    Args:
        root: Root node to search from
        pattern: Pattern to match (case-insensitive substring)

    Returns:
        List of matching ConfigNodes
    """
    matches: list[ConfigNode] = []
    pattern_lower = pattern.lower()

    def search(node: ConfigNode) -> None:
        if pattern_lower in node.path.lower() or pattern_lower in node.key.lower():
            matches.append(node)

        for child in node.children:
            search(child)

    search(root)
    return matches
