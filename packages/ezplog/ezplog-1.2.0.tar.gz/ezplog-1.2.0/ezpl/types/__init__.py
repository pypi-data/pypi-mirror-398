"""
Types module for Ezpl logging framework.

This module contains type definitions and enumerations.
"""

# =============================================================================
# IMPORTS
# =============================================================================

# ------------------------------------------------
# TYPE & ENUM DEFINITIONS
# ------------------------------------------------
from .log_level import LogLevel
from .patterns import (
    PATTERN_COLORS,
    Pattern,
    get_pattern_color,
    get_pattern_color_by_name,
)

# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # ------------------------------------------------
    # LOG LEVEL EXPORTS
    # ------------------------------------------------
    "LogLevel",
    # ------------------------------------------------
    # PATTERN EXPORTS
    # ------------------------------------------------
    "Pattern",
    "PATTERN_COLORS",
    "get_pattern_color",
    "get_pattern_color_by_name",
]
