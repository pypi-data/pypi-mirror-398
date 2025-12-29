"""Legal documents module for Obra.

Provides access to terms of service, privacy policy, and other legal documents
bundled with the package.
"""

from pathlib import Path
from typing import Optional

# Legal document versions - must match bundled documents
TERMS_VERSION = "2.1"
PRIVACY_VERSION = "1.3"

# Path to legal documents directory
LEGAL_DIR = Path(__file__).parent

# Document file paths
BETA_TERMS_PATH = LEGAL_DIR / "BETA_TERMS.txt"
TERMS_SUMMARY_PATH = LEGAL_DIR / "TERMS_SUMMARY.txt"


def get_beta_terms() -> str:
    """Get full Beta Software Agreement text.

    Returns:
        Full legal text of the Beta Software Agreement
    """
    with open(BETA_TERMS_PATH, encoding="utf-8") as f:
        return f.read()


def get_terms_summary() -> str:
    """Get the plain language summary of terms.

    Returns:
        Plain language summary suitable for display in terminal
    """
    with open(TERMS_SUMMARY_PATH, encoding="utf-8") as f:
        return f.read()


def get_terms_url() -> str:
    """Get URL to the full terms document.

    Returns:
        URL to obra.dev/terms
    """
    return "https://obra.dev/terms"


def get_privacy_url() -> str:
    """Get URL to the privacy policy document.

    Returns:
        URL to obra.dev/privacy
    """
    return "https://obra.dev/privacy"


__all__ = [
    "BETA_TERMS_PATH",
    "LEGAL_DIR",
    "PRIVACY_VERSION",
    "TERMS_SUMMARY_PATH",
    "TERMS_VERSION",
    "get_beta_terms",
    "get_privacy_url",
    "get_terms_summary",
    "get_terms_url",
]
