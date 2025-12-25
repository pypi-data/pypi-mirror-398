"""
Wizard module for Ezpl logging framework.

This module provides the RichWizard class for advanced Rich-based display
capabilities including panels, tables, JSON, and progress bars.
"""

# =============================================================================
# IMPORTS
# =============================================================================

# ------------------------------------------------
# WIZARD IMPLEMENTATION
# ------------------------------------------------
from .core import RichWizard

# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # ------------------------------------------------
    # WIZARD PUBLIC API
    # ------------------------------------------------
    "RichWizard",
]
