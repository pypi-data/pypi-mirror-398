"""
Git hooks for automatic HtmlGraph tracking.

This module provides templates and installation utilities for Git hooks
that automatically track development activity in HtmlGraph.
"""

from pathlib import Path

HOOKS_DIR = Path(__file__).parent

# Available hook templates
AVAILABLE_HOOKS = [
    "pre-commit",
    "post-commit",
    "post-checkout",
    "post-merge",
    "pre-push",
]

__all__ = ["HOOKS_DIR", "AVAILABLE_HOOKS"]
