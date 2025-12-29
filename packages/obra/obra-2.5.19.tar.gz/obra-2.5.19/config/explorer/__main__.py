"""Entry point for running the config explorer as a module.

Usage:
    python -m obra.config.explorer
"""

from obra.config.explorer.app import run_explorer

if __name__ == "__main__":
    run_explorer()
