"""
CLI utilities module for Ezpl logging framework.

This module contains utility functions and classes for CLI operations:
- Log parsing and analysis
- Statistics calculation
- User environment variable management
"""

# =============================================================================
# IMPORTS
# =============================================================================

# ------------------------------------------------
# ENVIRONMENT MANAGEMENT UTILITIES
# ------------------------------------------------
from .env_manager import UserEnvManager

# ------------------------------------------------
# LOG PARSING & STATISTICS UTILITIES
# ------------------------------------------------
from .log_parser import LogEntry, LogParser
from .log_stats import LogStatistics

# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # ------------------------------------------------
    # LOG UTILITIES EXPORTS
    # ------------------------------------------------
    "LogParser",
    "LogEntry",
    "LogStatistics",
    # ------------------------------------------------
    # ENVIRONMENT UTILITIES EXPORTS
    # ------------------------------------------------
    "UserEnvManager",
]
