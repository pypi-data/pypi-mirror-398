# ///////////////////////////////////////////////////////////////
# EZPL - File Logger Handler
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
File logger handler for Ezpl logging framework.

This module provides a file-based logging handler with advanced formatting,
session separation, and structured output.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# External libraries
from loguru import logger
from loguru._logger import Logger

# Internal modules
from ..core.exceptions import FileOperationError, LoggingError, ValidationError
from ..core.interfaces import LoggingHandler
from ..types import LogLevel
from .utils import safe_str_convert, sanitize_for_file

## ==> CLASSES
# ///////////////////////////////////////////////////////////////


class FileLogger(LoggingHandler):
    """
    File logger handler with advanced formatting and session management.

    This handler provides file-based logging with:
    - Structured log format
    - Session separators
    - HTML tag sanitization
    - Automatic file creation
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        log_file: Path | str,
        level: str = "INFO",
        rotation: Optional[str] = None,
        retention: Optional[str] = None,
        compression: Optional[str] = None,
    ) -> None:
        """
        Initialize the file logger handler.

        Args:
            log_file: Path to the log file
            level: The desired logging level
            rotation: Rotation size (e.g., "10 MB") or time (e.g., "1 day")
            retention: Retention period (e.g., "7 days")
            compression: Compression format (e.g., "zip", "gz")

        Raises:
            ValidationError: If the provided level is invalid
            FileOperationError: If file operations fail
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        self._level = level.upper()
        self._log_file = Path(log_file)
        self._logger = logger.bind(task="logger")
        self._logger_id = None
        self._rotation = rotation
        self._retention = retention
        self._compression = compression

        # Valider et créer le répertoire parent
        try:
            self._log_file.parent.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            raise FileOperationError(
                f"Cannot create log directory: {e}",
                str(self._log_file.parent),
                "create_directory",
            ) from e

        # Valider que le fichier peut être créé/écrit
        try:
            if not self._log_file.exists():
                self._log_file.touch()
            # Test d'écriture
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write("")
        except (PermissionError, OSError) as e:
            raise FileOperationError(
                f"Cannot write to log file: {e}", str(self._log_file), "write"
            ) from e

        self._initialize_logger()

    # ------------------------------------------------
    # PRIVATE HELPER METHODS
    # ------------------------------------------------

    def _initialize_logger(self) -> None:
        """
        Initialize the file logger handler.

        Raises:
            LoggingError: If logger initialization fails
        """
        try:
            if self._logger_id is not None:
                self._logger.remove(self._logger_id)

            # Préparer les paramètres pour loguru.add()
            add_kwargs = {
                "sink": self._log_file,
                "level": self._level,
                "format": self._custom_formatter,
                "filter": lambda record: record["extra"]["task"] == "logger",
                "encoding": "utf-8",
            }

            # Ajouter rotation si spécifiée
            if self._rotation:
                add_kwargs["rotation"] = self._rotation

            # Ajouter retention si spécifiée
            if self._retention:
                add_kwargs["retention"] = self._retention

            # Ajouter compression si spécifiée
            if self._compression:
                add_kwargs["compression"] = self._compression

            self._logger_id = self._logger.add(**add_kwargs)
        except Exception as e:
            raise LoggingError(f"Failed to initialize file logger: {e}", "file") from e

    # ///////////////////////////////////////////////////////////////
    # UTILS METHODS
    # ///////////////////////////////////////////////////////////////

    def set_level(self, level: str) -> None:
        """
        Set the logging level.

        Args:
            level: The desired logging level

        Raises:
            ValidationError: If the provided level is invalid
            LoggingError: If level update fails
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        try:
            self._level = level.upper()
            self._initialize_logger()
        except Exception as e:
            raise LoggingError(f"Failed to update log level: {e}", "file") from e

    def log(self, level: str, message: Any) -> None:
        """
        Log a message with the specified level.

        Args:
            level: The log level
            message: The message to log (any type, will be converted to string)

        Raises:
            ValidationError: If the level is invalid
            LoggingError: If logging fails
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        # Convertir message en string de manière robuste
        message = safe_str_convert(message)

        try:
            log_method = getattr(self._logger, level.lower())
            log_method(message)
        except Exception as e:
            raise LoggingError(f"Failed to log message: {e}", "file") from e

    # ///////////////////////////////////////////////////////////////
    # GETTER
    # ///////////////////////////////////////////////////////////////

    def get_logger(self) -> Logger:
        """
        Get the underlying Loguru logger instance.

        Returns:
            The Loguru logger instance

        Raises:
            LoggingError: If the logger is not initialized
        """
        if not self._logger:
            raise LoggingError("File logger not initialized", "file")
        return self._logger

    def get_log_file(self) -> Path:
        """
        Get the current log file path.

        Returns:
            Path to the log file
        """
        return self._log_file

    def get_file_size(self) -> int:
        """
        Get the current log file size in bytes.

        Returns:
            File size in bytes, or 0 if file doesn't exist or error occurs
        """
        try:
            if self._log_file.exists():
                return self._log_file.stat().st_size
            return 0
        except Exception:
            return 0

    def close(self) -> None:
        """
        Close the logger handler and release file handles.

        This method removes the loguru handler to release file handles,
        which is especially important on Windows where files can remain locked.
        """
        try:
            if self._logger_id is not None:
                # Remove the specific handler
                self._logger.remove(self._logger_id)
                self._logger_id = None

                # Force flush and close on Windows
                import sys
                import time

                if sys.platform == "win32":
                    # Force garbage collection to release file handles
                    import gc

                    gc.collect()
                    # Give Windows time to release file locks
                    time.sleep(0.1)
        except Exception as e:
            raise LoggingError("Failed to close logger", "file") from e

    # ///////////////////////////////////////////////////////////////
    # FILE OPERATIONS
    # ///////////////////////////////////////////////////////////////

    def add_separator(self) -> None:
        """
        Add a separator line to the log file for session distinction.

        Raises:
            FileOperationError: If writing to the log file fails
        """
        try:
            current_time = datetime.now().strftime("%Y-%m-%d - %H:%M")
            separator = f"\n\n## ==> {current_time}\n## /////////////////////////////////////////////////////////////////\n"
            with open(self._log_file, "a", encoding="utf-8") as log_file:
                log_file.write(separator)
        except Exception as e:
            raise FileOperationError(
                f"Failed to add separator to log file: {e}",
                str(self._log_file),
                "write",
            ) from e

    # ///////////////////////////////////////////////////////////////
    # FORMATTING METHODS
    # ///////////////////////////////////////////////////////////////

    def _custom_formatter(self, record: dict[str, Any]) -> str:
        """
        Custom formatter for file output.

        Args:
            record: Loguru record to format

        Returns:
            Formatted log message (toujours retourne une string, ne lève jamais d'exception)
        """
        try:
            level = (
                record.get("level", {}).name
                if hasattr(record.get("level", {}), "name")
                else "INFO"
            )
            log_level = LogLevel[level]
            return self._format_message(record, log_level)
        except Exception as e:
            # Ne jamais lever d'exception dans un formatter - retourner un message d'erreur sécurisé
            try:
                return f"????-??-?? ??:??:?? | FORMAT_ERR | unknown:unknown:? - [FORMAT ERROR: {type(e).__name__}]\n"
            except Exception:
                return "????-??-?? ??:??:?? | FORMAT_ERR | unknown:unknown:? - [FORMAT ERROR]\n"

    def _format_message(self, record: dict[str, Any], log_level: LogLevel) -> str:
        """
        Format a log message for file output.

        Args:
            record: Loguru record
            log_level: LogLevel enum instance

        Returns:
            Formatted log message (toujours retourne une string valide)
        """
        try:
            # Sécuriser le formatage du timestamp
            try:
                time_obj = record.get("time")
                if hasattr(time_obj, "strftime"):
                    timestamp = time_obj.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                timestamp = "????-??-?? ??:??:??"

            # Nettoyer le message de manière robuste
            message = safe_str_convert(record.get("message", ""))
            # Sanitizer pour fichier (supprime caractères problématiques)
            message = sanitize_for_file(message)

            # Nettoyer le nom de fonction
            fn = str(record.get("function", "unknown"))
            fn = fn.replace("<", "").replace(">", "")

            # Sécuriser module et line
            module = str(record.get("module", "unknown"))
            line = str(record.get("line", "?"))

            return (
                f"{timestamp} | "
                f"{log_level.label:<10} | "
                f"{module}:{fn}:{line} - "
                f"{message}\n"
            )
        except Exception as e:
            # Fallback sécurisé
            try:
                return f"????-??-?? ??:??:?? | FORMAT_ERR | unknown:unknown:? - [FORMAT ERROR: {type(e).__name__}]\n"
            except Exception:
                return "????-??-?? ??:??:?? | FORMAT_ERR | unknown:unknown:? - [FORMAT ERROR]\n"

    # ///////////////////////////////////////////////////////////////
    # REPRESENTATION METHODS
    # ///////////////////////////////////////////////////////////////

    def __str__(self) -> str:
        """String representation of the file logger."""
        return f"FileLogger(file={self._log_file}, level={self._level})"

    def __repr__(self) -> str:
        """Detailed string representation of the file logger."""
        return f"FileLogger(file={self._log_file}, level={self._level}, logger_id={self._logger_id})"
