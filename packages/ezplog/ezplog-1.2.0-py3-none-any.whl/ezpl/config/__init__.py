"""
Configuration module for Ezpl logging framework.

This module handles all configuration management.
"""

# =============================================================================
# IMPORTS
# =============================================================================

# ------------------------------------------------
# CONFIGURATION IMPLEMENTATIONS
# ------------------------------------------------
from .defaults import DefaultConfiguration
from .manager import ConfigurationManager

# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # ------------------------------------------------
    # CONFIGURATION PUBLIC API
    # ------------------------------------------------
    "ConfigurationManager",
    "DefaultConfiguration",
]
