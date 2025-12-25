"""
Core module for Ezpl logging framework.

This module contains the core business logic and interfaces.
"""

# =============================================================================
# IMPORTS
# =============================================================================

# ------------------------------------------------
# CORE EXCEPTIONS
# ------------------------------------------------
from .exceptions import (
    ConfigurationError,
    EzplError,
    FileOperationError,
    HandlerError,
    InitializationError,
    LoggingError,
    ValidationError,
)

# ------------------------------------------------
# CORE INTERFACES
# ------------------------------------------------
from .interfaces import (
    ConfigurationManager,
    EzplCore,
    IndentationManager,
    LoggingHandler,
)

# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # ------------------------------------------------
    # INTERFACE EXPORTS
    # ------------------------------------------------
    "LoggingHandler",
    "IndentationManager",
    "ConfigurationManager",
    "EzplCore",
    # ------------------------------------------------
    # EXCEPTION EXPORTS
    # ------------------------------------------------
    "EzplError",
    "ConfigurationError",
    "LoggingError",
    "ValidationError",
    "InitializationError",
    "FileOperationError",
    "HandlerError",
]
