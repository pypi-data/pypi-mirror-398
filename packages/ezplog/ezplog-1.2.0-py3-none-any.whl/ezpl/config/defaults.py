# ///////////////////////////////////////////////////////////////
# EZPL - Default Configuration
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Default configuration values for Ezpl logging framework.

This module defines all default configuration values used throughout the application.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
import os
import sys
from pathlib import Path
from typing import Any

## ==> FUNCTIONS
# ///////////////////////////////////////////////////////////////


def _get_app_data_dir() -> Path:
    """
    Get the application data directory (cross-platform).

    Returns:
        - Windows: %APPDATA% (Roaming)
        - Linux: ~/.local/share
        - macOS: ~/Library/Application Support
    """
    if sys.platform == "win32":
        # Windows: Use APPDATA (Roaming)
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "ezpl"
        # Fallback to user home
        return Path.home() / "AppData" / "Local" / "ezpl"
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support
        return Path.home() / "Library" / "Application Support" / "ezpl"
    else:
        # Linux: ~/.local/share
        return Path.home() / ".local" / "share" / "ezpl"


## ==> CLASSES
# ///////////////////////////////////////////////////////////////


class DefaultConfiguration:
    """
    Default configuration values for Ezpl.

    This class provides centralized access to all default configuration values.
    """

    # ///////////////////////////////////////////////////////////////
    # LOGGING DEFAULTS
    # ///////////////////////////////////////////////////////////////

    LOG_LEVEL = "INFO"
    LOG_FILE = "ezpl.log"
    # Use cross-platform app data directory for logs if no path specified
    LOG_DIR = _get_app_data_dir() / "logs"

    # ///////////////////////////////////////////////////////////////
    # PRINTER DEFAULTS
    # ///////////////////////////////////////////////////////////////

    PRINTER_LEVEL = "INFO"
    INDENT_STEP = 3
    INDENT_SYMBOL = ">"
    BASE_INDENT_SYMBOL = "~"

    # ///////////////////////////////////////////////////////////////
    # FILE LOGGER DEFAULTS
    # ///////////////////////////////////////////////////////////////

    FILE_LOGGER_LEVEL = "INFO"
    LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level:<10} | {module}:{function}:{line} - {message}"

    # Rotation settings (optional - None means no rotation)
    LOG_ROTATION = None  # e.g., "10 MB", "1 day", "500 KB", "12:00", "1 week"
    LOG_RETENTION = None  # e.g., "7 days", "1 month", "10 files"
    LOG_COMPRESSION = None  # e.g., "zip", "gz", "tar.gz"

    # ///////////////////////////////////////////////////////////////
    # CONFIGURATION DEFAULTS
    # ///////////////////////////////////////////////////////////////

    CONFIG_DIR = Path.home() / ".ezpl"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    # ///////////////////////////////////////////////////////////////
    # CLI DEFAULTS
    # ///////////////////////////////////////////////////////////////

    CLI_VERSION = "1.0.0"
    CLI_PROG_NAME = "Ezpl CLI"

    # ///////////////////////////////////////////////////////////////
    # EXPORT DEFAULTS
    # ///////////////////////////////////////////////////////////////

    EXPORT_BATCH_FILE = "export_env.bat"  # Windows
    EXPORT_SHELL_FILE = "export_env.sh"  # Unix/Linux/macOS

    # ///////////////////////////////////////////////////////////////
    # CLASS METHODS
    # ///////////////////////////////////////////////////////////////

    @classmethod
    def get_all_defaults(cls) -> dict[str, Any]:
        """
        Get all default configuration values as a dictionary.

        Returns:
            Dictionary containing all default configuration values
        """
        return {
            "log-level": cls.LOG_LEVEL,
            "log-file": cls.LOG_FILE,
            "log-dir": str(
                cls.LOG_DIR
            ),  # Convert Path to string for JSON serialization
            "printer-level": cls.PRINTER_LEVEL,
            "indent-step": cls.INDENT_STEP,
            "indent-symbol": cls.INDENT_SYMBOL,
            "base-indent-symbol": cls.BASE_INDENT_SYMBOL,
            "file-logger-level": cls.FILE_LOGGER_LEVEL,
            "log-format": cls.LOG_FORMAT,
            "log-rotation": cls.LOG_ROTATION,
            "log-retention": cls.LOG_RETENTION,
            "log-compression": cls.LOG_COMPRESSION,
            "cli-version": cls.CLI_VERSION,
            "cli-prog-name": cls.CLI_PROG_NAME,
        }

    @classmethod
    def get_logging_defaults(cls) -> dict[str, Any]:
        """
        Get logging-specific default values.

        Returns:
            Dictionary containing logging default values
        """
        return {
            "log-level": cls.LOG_LEVEL,
            "log-file": cls.LOG_FILE,
            "log-dir": cls.LOG_DIR,
        }

    @classmethod
    def get_printer_defaults(cls) -> dict[str, Any]:
        """
        Get printer-specific default values.

        Returns:
            Dictionary containing printer default values
        """
        return {
            "printer-level": cls.PRINTER_LEVEL,
            "indent-step": cls.INDENT_STEP,
            "indent-symbol": cls.INDENT_SYMBOL,
            "base-indent-symbol": cls.BASE_INDENT_SYMBOL,
        }

    @classmethod
    def get_file_logger_defaults(cls) -> dict[str, Any]:
        """
        Get file logger-specific default values.

        Returns:
            Dictionary containing file logger default values
        """
        return {
            "file-logger-level": cls.FILE_LOGGER_LEVEL,
            "log-format": cls.LOG_FORMAT,
            "log-rotation": cls.LOG_ROTATION,
            "log-retention": cls.LOG_RETENTION,
            "log-compression": cls.LOG_COMPRESSION,
        }
