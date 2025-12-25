"""
Handlers module for Ezpl logging framework.

This module contains concrete implementations of logging handlers.
"""

# =============================================================================
# IMPORTS
# =============================================================================

# ------------------------------------------------
# HANDLER IMPLEMENTATIONS
# ------------------------------------------------
from .console import ConsolePrinter, ConsolePrinterWrapper
from .file import FileLogger
from .wizard import RichWizard

# ------------------------------------------------
# BACKWARD COMPATIBILITY ALIASES
# ------------------------------------------------
EzPrinter = ConsolePrinter
EzLogger = FileLogger

# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # ------------------------------------------------
    # HANDLER CLASS EXPORTS
    # ------------------------------------------------
    "ConsolePrinter",
    "ConsolePrinterWrapper",
    "FileLogger",
    "RichWizard",
    # ------------------------------------------------
    # BACKWARD COMPATIBILITY EXPORTS
    # ------------------------------------------------
    "EzPrinter",
    "EzLogger",
]
