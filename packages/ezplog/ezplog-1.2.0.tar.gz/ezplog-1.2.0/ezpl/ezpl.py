# ///////////////////////////////////////////////////////////////
# EZPL - Main logging singleton
# Project: ezpl
# ///////////////////////////////////////////////////////////////

from __future__ import annotations

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
import sys
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TypeVar

# External libraries
from loguru import logger
from loguru._logger import Logger

# Internal modules
from .config import ConfigurationManager
from .handlers import EzLogger, EzPrinter
from .handlers.console import ConsolePrinterWrapper

## ==> GLOBALS
# ///////////////////////////////////////////////////////////////
APP_PATH = Path(sys.argv[0]).parent

## ==> VARIABLES
# ///////////////////////////////////////////////////////////////

## ==> CLASSES
# ///////////////////////////////////////////////////////////////


T = TypeVar("T", bound="Ezpl")


class Ezpl:
    _instance: Ezpl | None = None
    _lock: threading.Lock = threading.Lock()
    _config_locked: bool = False
    _log_file: Path
    _printer: EzPrinter
    _logger: EzLogger
    _config_manager: ConfigurationManager

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Return True if the Ezpl singleton has already been created.

        Useful for libraries that want to know whether they are the first
        to initialize Ezpl or if they should avoid re-configuring it.
        """
        return cls._instance is not None

    def __new__(
        cls: type[T],
        log_file: Path | str = None,
        log_level: str = None,
        printer_level: str = None,
        file_logger_level: str = None,
        log_rotation: str = None,
        log_retention: str = None,
        log_compression: str = None,
        indent_step: int = None,
        indent_symbol: str = None,
        base_indent_symbol: str = None,
    ) -> T:
        """
        Creates and returns a new instance of Ezpl if none exists.

        **Notes:**
        Ensures only one instance of Ezpl exists (Singleton pattern).

        **Priority order for configuration (for each parameter):**
        1. Arguments passed directly (highest priority)
        2. Environment variables (EZPL_*)
        3. Configuration file (~/.ezpl/config.json)
        4. Default values (lowest priority)

        **Args:**

            * `log_file` (Path | str, optional): Path to the log file
            * `log_level` (str, optional): Global log level (applies to both printer and logger)
            * `printer_level` (str, optional): Printer log level
            * `file_logger_level` (str, optional): File logger level
            * `log_rotation` (str, optional): Rotation setting (e.g., "10 MB", "1 day")
            * `log_retention` (str, optional): Retention period (e.g., "7 days")
            * `log_compression` (str, optional): Compression format (e.g., "zip", "gz")
            * `indent_step` (int, optional): Indentation step size
            * `indent_symbol` (str, optional): Symbol for indentation
            * `base_indent_symbol` (str, optional): Base indentation symbol

        **Returns:**

            * `Ezpl`: The singleton instance of the Ezpl class.

        **Raises:**

            * `None`.
        """

        # //////
        # Double-checked locking pattern for thread-safe singleton
        if cls._instance is None:
            with cls._lock:
                # Check again after acquiring lock (double-checked locking)
                if cls._instance is None:
                    logger.remove()

                    # Initialize configuration manager
                    cls._config_manager = ConfigurationManager()

                    # Determine configuration values with priority: arg > env > config file > default
                    # Helper function to get value with priority order
                    def get_config_value(
                        arg_value, config_key: str, getter_method
                    ) -> Any:
                        """
                        Get configuration value with priority: arg > env > config file > default

                        Args:
                            arg_value: Value from argument (can be None)
                            config_key: Configuration key name
                            getter_method: Method to get default value from config manager

                        Returns:
                            Final configuration value
                        """
                        # Priority 1: Argument direct
                        if arg_value is not None:
                            return arg_value

                        # Priority 2: Environment variable (already loaded in config_manager)
                        # Priority 3: Config file (already loaded in config_manager)
                        # Priority 4: Default (via getter method)
                        # The config_manager already has the correct priority (env > file > default)
                        config_value = cls._config_manager.get(config_key)
                        if config_value is not None:
                            return config_value

                        # Fallback to default via getter
                        return getter_method()

                    # Log file
                    if log_file:
                        cls._log_file = Path(log_file)
                    else:
                        cls._log_file = cls._config_manager.get_log_file()

                    # Log level (global)
                    final_log_level = get_config_value(
                        log_level, "log-level", cls._config_manager.get_log_level
                    )

                    # Printer level
                    final_printer_level = get_config_value(
                        printer_level,
                        "printer-level",
                        cls._config_manager.get_printer_level,
                    )

                    # File logger level
                    final_file_logger_level = get_config_value(
                        file_logger_level,
                        "file-logger-level",
                        cls._config_manager.get_file_logger_level,
                    )

                    # Rotation settings (can be None)
                    # Priority: arg > env > config file > default
                    # Note: If arg is None (default), we check env/config/default
                    # If user wants to explicitly set None, they can pass None or use configure()
                    final_rotation = (
                        log_rotation
                        if log_rotation is not None
                        else cls._config_manager.get_log_rotation()
                    )
                    final_retention = (
                        log_retention
                        if log_retention is not None
                        else cls._config_manager.get_log_retention()
                    )
                    final_compression = (
                        log_compression
                        if log_compression is not None
                        else cls._config_manager.get_log_compression()
                    )

                    # Indent settings
                    final_indent_step = get_config_value(
                        indent_step, "indent-step", cls._config_manager.get_indent_step
                    )
                    final_indent_symbol = get_config_value(
                        indent_symbol,
                        "indent-symbol",
                        cls._config_manager.get_indent_symbol,
                    )
                    final_base_indent_symbol = get_config_value(
                        base_indent_symbol,
                        "base-indent-symbol",
                        cls._config_manager.get_base_indent_symbol,
                    )

                    cls._instance = super().__new__(cls)

                    # Initialize printer with resolved configuration
                    cls._printer = EzPrinter(
                        level=final_printer_level,
                        indent_step=final_indent_step,
                        indent_symbol=final_indent_symbol,
                        base_indent_symbol=final_base_indent_symbol,
                    )

                    # Initialize logger with resolved configuration
                    cls._logger = EzLogger(
                        log_file=cls._log_file,
                        level=final_file_logger_level,
                        rotation=final_rotation,
                        retention=final_retention,
                        compression=final_compression,
                    )

                    # Apply global log level if specified, but only if specific levels were not set
                    # Priority: printer_level/file_logger_level > log_level
                    if final_log_level:
                        # Only apply global level if specific levels were not provided
                        if printer_level is None and file_logger_level is None:
                            cls._instance.set_level(final_log_level)
                        elif printer_level is None:
                            # Only apply to printer if printer_level was not specified
                            cls._instance.set_printer_level(final_log_level)
                        elif file_logger_level is None:
                            # Only apply to logger if file_logger_level was not specified
                            cls._instance.set_logger_level(final_log_level)

        return cls._instance

    # ///////////////////////////////////////////////////////////////
    # GETTER
    # ///////////////////////////////////////////////////////////////

    def get_printer(self) -> ConsolePrinterWrapper:
        """
        Returns the Printer wrapper instance (compatible with existing API).

        **Returns:**

            * ConsolePrinterWrapper: Wrapper providing info(), debug(), success(), etc.

        **Raises:**

            * `None`.
        """
        return self._printer.get_printer()

    # ///////////////////////////////////////////////////////////////

    def get_logger(self) -> Logger:
        """
        Returns the FileLogger instance (loguru Logger).

        **Returns:**

            * loguru.Logger: The loguru logger instance for file logging.

        **Raises:**

            * `None`.
        """
        return self._logger.get_logger()

    # ///////////////////////////////////////////////////////////////
    # UTILS METHODS
    # ///////////////////////////////////////////////////////////////

    def set_level(self, level: str) -> None:
        """
        Définit le niveau de log du printer et du logger en même temps (méthode de compatibilité).

        **Args:**

            * `level` (str): Le niveau de log désiré (ex: "INFO", "WARNING").

        **Returns:**

            * `None`.
        """
        self.set_logger_level(level)
        self.set_printer_level(level)

    def set_printer_level(self, level: str) -> None:
        """
        Définit le niveau de log du printer uniquement.

        **Args:**

            * `level` (str): Le niveau de log désiré pour le printer.

        **Returns:**

            * `None`.
        """
        self._printer.set_level(level)

    def set_logger_level(self, level: str) -> None:
        """
        Définit le niveau de log du logger uniquement.

        **Args:**

            * `level` (str): Le niveau de log désiré pour le logger.

        **Returns:**

            * `None`.
        """
        self._logger.set_level(level)

    # ///////////////////////////////////////////////////////////////

    def add_separator(self) -> None:
        """
        Adds a separator to the log file.

        **Returns:**

            * `None`.
        """
        self._logger.add_separator()

    # ///////////////////////////////////////////////////////////////

    @contextmanager
    def manage_indent(self) -> Generator[None, None, None]:
        """
        Context manager to manage indentation level.

        **Returns:**

            * `None`.
        """
        with self._printer.manage_indent():
            yield

    # ///////////////////////////////////////////////////////////////
    # ENHANCED METHODS
    # ///////////////////////////////////////////////////////////////

    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton instance (useful for testing).

        Warning: This will destroy the current instance and all its state.
        """
        if cls._instance is not None:
            # Close logger handlers to release file handles (important on Windows)
            try:
                if hasattr(cls._instance, "_logger") and cls._instance._logger:
                    cls._instance._logger.close()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            cls._instance = None
        # Also reset configuration lock
        cls._config_locked = False

    # ------------------------------------------------
    # CONFIG LOCK CONTROL
    # ------------------------------------------------

    @classmethod
    def lock_config(cls) -> None:
        """
        Lock Ezpl configuration so that future configure() calls are ignored
        unless explicitly forced.

        Intended usage:
            1. Root application configures Ezpl once
            2. Calls Ezpl.lock_config()
            3. Libraries calling configure() later will not override settings
        """
        cls._config_locked = True

    @classmethod
    def unlock_config(cls) -> None:
        """
        Unlock Ezpl configuration.

        Use with care: this allows configure() to change global logging
        configuration again.
        """
        cls._config_locked = False

    def set_log_file(self, log_file: Path | str) -> None:
        """
        Change the log file (requires reinitialization of the logger).

        Args:
            log_file: New path to the log file

        Note: This will reinitialize the file logger but keep the singleton instance.
        """
        new_log_file = Path(log_file)
        if new_log_file != self._log_file:
            self._log_file = new_log_file
            # Update configuration
            self._config_manager.set("log-file", str(new_log_file))
            # Safely close previous logger to avoid duplicated loguru handlers
            try:
                if hasattr(self, "_logger") and self._logger:
                    self._logger.close()
            except Exception as e:
                logger.error(f"Error while closing previous logger: {e}")
            # Reinitialize logger with the new file and current parameters
            self._logger = EzLogger(
                log_file=self._log_file,
                level=self._logger._level,
                rotation=self._config_manager.get_log_rotation(),
                retention=self._config_manager.get_log_retention(),
                compression=self._config_manager.get_log_compression(),
            )

    def get_log_file(self) -> Path:
        """
        Get the current log file path.

        Returns:
            Path to the current log file
        """
        return self._log_file

    def get_config(self) -> ConfigurationManager:
        """
        Get the current configuration manager.

        Returns:
            ConfigurationManager instance for accessing and modifying configuration
        """
        return self._config_manager

    def reload_config(self) -> None:
        """
        Reload configuration from file and environment variables.

        This method reloads the configuration and reapplies it to handlers.
        Useful when environment variables or the config file have changed
        after the singleton was initialized.

        Note: This will reinitialize handlers with the new configuration.
        """
        # Reload configuration
        self._config_manager.reload()

        # Get configuration values
        printer_level = self._config_manager.get_printer_level()
        file_logger_level = self._config_manager.get_file_logger_level()
        global_log_level = self._config_manager.get_log_level()

        # Check if specific levels are explicitly set (not just defaults)
        # Priority: specific levels > global level
        # Only apply global level if specific levels are not explicitly set
        printer_level_explicit = self._config_manager.has_key("printer-level")
        file_logger_level_explicit = self._config_manager.has_key("file-logger-level")
        global_log_level_explicit = self._config_manager.has_key("log-level")

        # Reapply to handlers with priority logic
        if printer_level_explicit and file_logger_level_explicit:
            # Both specific levels are explicitly set, use them
            self.set_printer_level(printer_level)
            self.set_logger_level(file_logger_level)
        elif printer_level_explicit:
            # Only printer level is explicitly set
            self.set_printer_level(printer_level)
            # Apply global level to logger if it's explicitly set, otherwise use file_logger_level
            if global_log_level_explicit:
                self.set_logger_level(global_log_level)
            else:
                self.set_logger_level(file_logger_level)
        elif file_logger_level_explicit:
            # Only file logger level is explicitly set
            self.set_logger_level(file_logger_level)
            # Apply global level to printer if it's explicitly set, otherwise use printer_level
            if global_log_level_explicit:
                self.set_printer_level(global_log_level)
            else:
                self.set_printer_level(printer_level)
        elif global_log_level_explicit:
            # Only global level is explicitly set, apply to both
            self.set_level(global_log_level)
        else:
            # No explicit levels, use defaults (shouldn't happen, but safe fallback)
            self.set_printer_level(printer_level)
            self.set_logger_level(file_logger_level)

        # Reinitialize logger with new rotation / retention / compression settings
        # Preserve current level if logger was already initialized
        current_logger_level = (
            self._logger._level
            if hasattr(self, "_logger") and self._logger
            else file_logger_level
        )
        try:
            if hasattr(self, "_logger") and self._logger:
                self._logger.close()
        except Exception as e:
            logger.error(f"Error while closing logger during reload_config: {e}")
        self._logger = EzLogger(
            log_file=self._log_file,
            level=current_logger_level,
            rotation=self._config_manager.get_log_rotation(),
            retention=self._config_manager.get_log_retention(),
            compression=self._config_manager.get_log_compression(),
        )

        # Reinitialize printer with new indent settings
        # Preserve current level if printer was already initialized
        current_printer_level = (
            self._printer._level
            if hasattr(self, "_printer") and self._printer
            else printer_level
        )
        self._printer = EzPrinter(
            level=current_printer_level,
            indent_step=self._config_manager.get_indent_step(),
            indent_symbol=self._config_manager.get_indent_symbol(),
            base_indent_symbol=self._config_manager.get_base_indent_symbol(),
        )

    def configure(self, config_dict: dict[str, Any] = None, **kwargs) -> None:
        """
        Configure Ezpl dynamically.

        Args:
            config_dict: Dictionary of configuration values to update
            **kwargs: Configuration options (alternative to config_dict):
                - log_file or log-file: Path to log file
                - printer_level or printer-level: Printer log level
                - logger_level or file-logger-level: File logger level
                - level or log-level: Set both printer and logger level
                - log_rotation or log-rotation: Rotation setting (e.g., "10 MB", "1 day")
                - log_retention or log-retention: Retention period (e.g., "7 days")
                - log_compression or log-compression: Compression format (e.g., "zip", "gz")
                - indent_step or indent-step: Indentation step size
                - indent_symbol or indent-symbol: Symbol for indentation
                - base_indent_symbol or base-indent-symbol: Base indentation symbol

        Note: Changes are persisted to the configuration file.
        """
        # Merge config_dict and kwargs
        if config_dict:
            kwargs.update(config_dict)

        # Special control flag (not stored in configuration):
        # - force=True allows configure() even when configuration is locked
        force = kwargs.pop("force", False)

        # If configuration is locked and not forced, ignore configure() call
        if self._config_locked and not force:
            return

        # Normalize keys: convert underscores to hyphens for consistency
        normalized_config = {}
        key_mapping = {
            "log_file": "log-file",
            "printer_level": "printer-level",
            "logger_level": "file-logger-level",
            "level": "log-level",
            "log_rotation": "log-rotation",
            "log_retention": "log-retention",
            "log_compression": "log-compression",
            "indent_step": "indent-step",
            "indent_symbol": "indent-symbol",
            "base_indent_symbol": "base-indent-symbol",
        }

        for key, value in kwargs.items():
            # Use normalized key if mapping exists, otherwise keep original
            normalized_key = key_mapping.get(key, key)
            normalized_config[normalized_key] = value

        # Update configuration manager
        self._config_manager.update(normalized_config)
        self._config_manager.save()

        # Apply changes to handlers
        if "log-file" in normalized_config:
            self.set_log_file(normalized_config["log-file"])

        # Handle log level changes with proper priority
        # Priority: specific levels (printer-level, file-logger-level) > global level (log-level)
        has_printer_level = "printer-level" in normalized_config
        has_file_logger_level = "file-logger-level" in normalized_config
        has_global_level = "log-level" in normalized_config

        if has_printer_level and has_file_logger_level:
            # Both specific levels are provided, use them
            self.set_printer_level(normalized_config["printer-level"])
            self.set_logger_level(normalized_config["file-logger-level"])
        elif has_printer_level:
            # Only printer level is provided
            self.set_printer_level(normalized_config["printer-level"])
            # Apply global level to logger if provided, otherwise leave it unchanged
            if has_global_level:
                self.set_logger_level(normalized_config["log-level"])
        elif has_file_logger_level:
            # Only file logger level is provided
            self.set_logger_level(normalized_config["file-logger-level"])
            # Apply global level to printer if provided, otherwise leave it unchanged
            if has_global_level:
                self.set_printer_level(normalized_config["log-level"])
        elif has_global_level:
            # Only global level is provided, apply to both
            self.set_level(normalized_config["log-level"])

        # Reinitialize logger if rotation settings changed
        rotation_changed = any(
            key in normalized_config
            for key in ["log-rotation", "log-retention", "log-compression"]
        )
        if rotation_changed:
            # Save current level before closing logger
            current_logger_level = (
                self._logger._level
                if hasattr(self, "_logger") and self._logger
                else self._config_manager.get_file_logger_level()
            )
            # Close previous logger before creating a new one to avoid duplicate handlers
            try:
                if hasattr(self, "_logger") and self._logger:
                    self._logger.close()
            except Exception as e:
                logger.error(f"Error while closing logger during configure(): {e}")
            self._logger = EzLogger(
                log_file=self._log_file,
                level=self._config_manager.get_file_logger_level()
                or current_logger_level,
                rotation=self._config_manager.get_log_rotation(),
                retention=self._config_manager.get_log_retention(),
                compression=self._config_manager.get_log_compression(),
            )

        # Reinitialize printer if indent settings changed
        indent_changed = any(
            key in normalized_config
            for key in ["indent-step", "indent-symbol", "base-indent-symbol"]
        )
        if indent_changed:
            # Save current level before reinitializing printer
            current_printer_level = (
                self._printer._level
                if hasattr(self, "_printer") and self._printer
                else self._config_manager.get_printer_level()
            )
            self._printer = EzPrinter(
                level=self._config_manager.get_printer_level() or current_printer_level,
                indent_step=self._config_manager.get_indent_step(),
                indent_symbol=self._config_manager.get_indent_symbol(),
                base_indent_symbol=self._config_manager.get_base_indent_symbol(),
            )
