"""
Ezpl - Modern Python logging framework.

Ezpl is a modern Python library for advanced log management, using **Rich**
for console output and **loguru** for file logging, with a simple and typed API,
suitable for professional and industrial applications.

**Main Features:**
    - Singleton pattern for global logging instance
    - Rich-based console output with colors and formatting
    - Loguru-based file logging with rotation support
    - Contextual indentation management
    - Pattern-based logging (SUCCESS, ERROR, WARN, TIP, etc.)
    - JSON display support
    - Robust error handling

**Quick Start:**
    >>> from ezpl import Ezpl
    >>> ezpl = Ezpl()
    >>> printer = ezpl.get_printer()
    >>> logger = ezpl.get_logger()
    >>> printer.info("Hello, Ezpl!")
    >>> logger.info("Logged to file")
"""

from __future__ import annotations

import sys

# =============================================================================
# META INFORMATIONS
# =============================================================================

__version__ = "1.2.0"
__author__ = "Neuraaak"
__maintainer__ = "Neuraaak"
__license__ = "MIT"
__description__ = "A module for easier logging"
__keywords__ = ["logging", "rich", "loguru", "console", "file"]
__url__ = "https://github.com/neuraaak/ezpl"
__repository__ = "https://github.com/neuraaak/ezpl"
__python_requires__ = ">=3.10"

# =============================================================================
# PYTHON VERSION CHECK
# =============================================================================

if sys.version_info < (3, 10):
    raise RuntimeError(
        f"ezpl {__version__} requires Python 3.10 or higher. "
        f"Current version: {sys.version}"
    )

# =============================================================================
# IMPORTS
# =============================================================================

# ------------------------------------------------
# CORE CONFIG & EXCEPTIONS
# ------------------------------------------------
from .config import ConfigurationManager
from .core.exceptions import (
    ConfigurationError,
    EzplError,
    FileOperationError,
    HandlerError,
    InitializationError,
    LoggingError,
    ValidationError,
)

# ------------------------------------------------
# MAIN CLASS & HANDLERS
# ------------------------------------------------
from .ezpl import Ezpl
from .handlers import ConsolePrinter, EzLogger, EzPrinter, FileLogger, RichWizard
from .handlers.console import ConsolePrinterWrapper

# ------------------------------------------------
# TYPES
# ------------------------------------------------
from .types import (
    PATTERN_COLORS,
    LogLevel,
    Pattern,
    get_pattern_color,
    get_pattern_color_by_name,
)

# =============================================================================
# TYPE ALIASES
# =============================================================================

# Canonical type aliases for users.
# They mirror the internal EzPrinter / EzLogger types.

# ------------------------------------------------
# PRINTER TYPE ALIAS
# ------------------------------------------------
Printer = EzPrinter
"""Type alias for EzPrinter (console printer handler).
Use this type when you want to annotate a variable that represents a printer.

Example:
    >>> from ezpl import Ezpl, Printer
    >>> ezpl = Ezpl()
    >>> printer: Printer = ezpl.get_printer()
    >>> printer.info("Hello!")
    >>> printer.success("Done!")
    >>> printer.print_json({"key": "value"})
"""

# ------------------------------------------------
# LOGGER TYPE ALIAS
# ------------------------------------------------
Logger = EzLogger
"""Type alias for EzLogger (file logger handler).
Use this type when you want to annotate a variable that represents a logger.

Example:
    >>> from ezpl import Ezpl, Logger
    >>> ezpl = Ezpl()
    >>> logger: Logger = ezpl.get_logger()
    >>> logger.info("Logged to file")
"""

# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # ------------------------------------------------
    # MAIN CLASS EXPORTS
    # ------------------------------------------------
    "Ezpl",
    # ------------------------------------------------
    # HANDLER CLASS EXPORTS
    # ------------------------------------------------
    "EzPrinter",
    "EzLogger",
    "Logger",
    "ConsolePrinter",
    "FileLogger",
    "ConsolePrinterWrapper",
    "RichWizard",
    # ------------------------------------------------
    # CONFIGURATION EXPORTS
    # ------------------------------------------------
    "ConfigurationManager",
    # ------------------------------------------------
    # TYPE ALIASES EXPORTS
    # ------------------------------------------------
    "Printer",
    # ------------------------------------------------
    # TYPE & PATTERN EXPORTS
    # ------------------------------------------------
    "LogLevel",
    "Pattern",
    "PATTERN_COLORS",
    "get_pattern_color",
    "get_pattern_color_by_name",
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
    # ------------------------------------------------
    # METADATA EXPORTS
    # ------------------------------------------------
    "__version__",
    "__author__",
    "__maintainer__",
    "__license__",
    "__description__",
    "__keywords__",
    "__url__",
    "__repository__",
    "__python_requires__",
]
