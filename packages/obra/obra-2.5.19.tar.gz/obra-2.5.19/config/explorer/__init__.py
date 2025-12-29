"""Configuration Explorer TUI for Obra.

This module provides an interactive terminal-based configuration browser
using Textual. Users can navigate, search, and modify Obra settings through
a visual tree interface.

Usage:
    obra config explore
    # or in interactive mode:
    /config explore
"""

from obra.config.explorer.app import ConfigExplorerApp, run_explorer

__all__ = ["ConfigExplorerApp", "run_explorer"]
