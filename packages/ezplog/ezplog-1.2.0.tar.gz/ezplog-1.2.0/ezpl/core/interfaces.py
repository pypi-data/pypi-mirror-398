# ///////////////////////////////////////////////////////////////
# EZPL - Core Interfaces
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Core interfaces for Ezpl logging framework.

This module defines the core interfaces and protocols used throughout the application.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
from abc import ABC, abstractmethod
from collections.abc import Generator
from pathlib import Path
from typing import Any, Protocol

## ==> CLASSES
# ///////////////////////////////////////////////////////////////


class LoggingHandler(Protocol):
    """
    Protocol for logging handlers.

    This protocol defines the interface that all logging handlers must implement.
    """

    def log(self, level: str, message: str) -> None:
        """Log a message with the specified level."""
        ...

    def set_level(self, level: str) -> None:
        """Set the logging level."""
        ...


class IndentationManager(Protocol):
    """
    Protocol for indentation management.

    This protocol defines the interface for managing indentation levels.
    """

    def get_indent(self) -> str:
        """Get the current indentation string."""
        ...

    def add_indent(self) -> None:
        """Increase the indentation level."""
        ...

    def del_indent(self) -> None:
        """Decrease the indentation level."""
        ...

    def reset_indent(self) -> None:
        """Reset the indentation level to zero."""
        ...

    def manage_indent(self) -> Generator[None, None, None]:
        """Context manager for temporary indentation."""
        ...


class ConfigurationManager(Protocol):
    """
    Protocol for configuration management.

    This protocol defines the interface for configuration managers.
    """

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        ...

    def get_log_level(self) -> str:
        """Get the current log level."""
        ...

    def get_log_file(self) -> Path:
        """Get the current log file path."""
        ...

    def get_printer_level(self) -> str:
        """Get the current printer level."""
        ...

    def get_file_logger_level(self) -> str:
        """Get the current file logger level."""
        ...

    def save(self) -> None:
        """Save configuration to file."""
        ...


class EzplCore(ABC):
    """
    Abstract base class for the core Ezpl functionality.

    This abstract class defines the interface for the main Ezpl class.
    """

    # ///////////////////////////////////////////////////////////////
    # ABSTRACT METHODS
    # ///////////////////////////////////////////////////////////////

    @abstractmethod
    def get_printer(self) -> LoggingHandler:
        """Get the printer handler."""
        ...

    @abstractmethod
    def get_logger(self) -> LoggingHandler:
        """Get the file logger handler."""
        ...

    @abstractmethod
    def set_level(self, level: str) -> None:
        """Set the logging level for both printer and logger."""
        ...

    @abstractmethod
    def set_printer_level(self, level: str) -> None:
        """Set the printer logging level."""
        ...

    @abstractmethod
    def set_logger_level(self, level: str) -> None:
        """Set the file logger level."""
        ...

    @abstractmethod
    def add_separator(self) -> None:
        """Add a separator to the log file."""
        ...

    @abstractmethod
    def manage_indent(self) -> Generator[None, None, None]:
        """Context manager for indentation management."""
        ...
