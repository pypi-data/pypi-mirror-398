# ///////////////////////////////////////////////////////////////
# EZPL - Console Printer Handler
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Console printer handler for Ezpl logging framework.

This module provides a console-based logging handler with advanced formatting,
indentation management, and color support using Rich.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Optional, Union

# External libraries
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

# Internal modules
from ..core.exceptions import ValidationError
from ..core.interfaces import IndentationManager, LoggingHandler
from ..types import LogLevel, Pattern, get_pattern_color
from .utils import safe_str_convert, sanitize_for_console
from .wizard import RichWizard

## ==> CLASSES
# ///////////////////////////////////////////////////////////////


class ConsolePrinterWrapper:
    """
    Wrapper pour compatibilité avec l'API existante.

    Permet d'utiliser printer.info(), printer.debug(), etc.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, console_printer: "ConsolePrinter") -> None:
        self._console_printer = console_printer

    # ///////////////////////////////////////////////////////////////
    # LOGGING METHODS (API primaire)
    # ///////////////////////////////////////////////////////////////

    def info(self, message: Any) -> None:
        """Log an info message with pattern format."""
        self._console_printer.print_pattern(Pattern.INFO, message, "INFO")

    def debug(self, message: Any) -> None:
        """Log a debug message with pattern format."""
        self._console_printer.print_pattern(Pattern.DEBUG, message, "DEBUG")

    def success(self, message: Any) -> None:
        """Log a success message with pattern format."""
        self._console_printer.print_pattern(Pattern.SUCCESS, message, "INFO")

    def warning(self, message: Any) -> None:
        """Log a warning message with pattern format."""
        self._console_printer.print_pattern(Pattern.WARN, message, "WARNING")

    def warn(self, message: Any) -> None:
        """Log a warning message with pattern format (alias for warning)."""
        self.warning(message)

    def error(self, message: Any) -> None:
        """Log an error message with pattern format."""
        self._console_printer.print_pattern(Pattern.ERROR, message, "ERROR")

    def critical(self, message: Any) -> None:
        """Log a critical message with pattern format."""
        self._console_printer.print_pattern(Pattern.ERROR, message, "CRITICAL")

    # ------------------------------------------------
    # ADDITIONAL PATTERN METHODS
    # ------------------------------------------------

    def tip(self, message: Any) -> None:
        """Display a tip message with pattern format."""
        self._console_printer.print_pattern(Pattern.TIP, message, "INFO")

    def system(self, message: Any) -> None:
        """Display a system message with pattern format."""
        self._console_printer.print_pattern(Pattern.SYSTEM, message, "INFO")

    def install(self, message: Any) -> None:
        """Display an installation message with pattern format."""
        self._console_printer.print_pattern(Pattern.INSTALL, message, "INFO")

    def detect(self, message: Any) -> None:
        """Display a detection message with pattern format."""
        self._console_printer.print_pattern(Pattern.DETECT, message, "INFO")

    def config(self, message: Any) -> None:
        """Display a configuration message with pattern format."""
        self._console_printer.print_pattern(Pattern.CONFIG, message, "INFO")

    def deps(self, message: Any) -> None:
        """Display a dependencies message with pattern format."""
        self._console_printer.print_pattern(Pattern.DEPS, message, "INFO")

    # ------------------------------------------------
    # ENHANCED METHODS
    # ------------------------------------------------

    def print_pattern(
        self, pattern: Union[str, Pattern], message: Any, level: str = "INFO"
    ) -> None:
        """Display a message with pattern format: • PATTERN :: message"""
        self._console_printer.print_pattern(pattern, message, level)

    def print_json(
        self,
        data: Union[str, dict, list],
        title: Optional[str] = None,
        indent: Optional[int] = None,
        highlight: bool = True,
    ) -> None:
        """Display JSON data in a formatted and syntax-highlighted way."""
        self._console_printer.print_json(data, title, indent, highlight)

    # ------------------------------------------------
    # WIZARD ACCESS
    # ------------------------------------------------

    @property
    def wizard(self) -> "RichWizard":
        """
        Get the Rich Wizard instance for advanced display features.

        Returns:
            RichWizard instance for panels, tables, JSON, etc.

        Example:
            >>> printer.wizard.success_panel("Success", "Operation completed")
            >>> printer.wizard.status_table("Status", data)
            >>> printer.wizard.dependency_table({"tool": "1.0.0"})
        """
        return self._console_printer._wizard

    # ------------------------------------------------
    # DELEGATION TO CONSOLE PRINTER
    # ------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to the underlying ConsolePrinter.

        This allows the wrapper to transparently expose indentation methods
        and other attributes from ConsolePrinter.

        Args:
            name: Attribute name to access

        Returns:
            The requested attribute from ConsolePrinter
        """
        return getattr(self._console_printer, name)


class ConsolePrinter(LoggingHandler, IndentationManager):
    """
    Console printer handler with advanced formatting and indentation support using Rich.

    This handler provides console-based logging with:
    - Color-coded log levels using Rich
    - Indentation management
    - Robust character handling (Rich handles special characters automatically)
    - Context manager support
    """

    MAX_INDENT = 10  # Limite maximale d'indentation

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        level: str = "INFO",
        indent_step: int = 3,
        indent_symbol: str = ">",
        base_indent_symbol: str = "~",
    ) -> None:
        """
        Initialize the console printer handler.

        Args:
            level: The desired logging level
            indent_step: Number of spaces for each indentation level
            indent_symbol: Symbol for indentation levels
            base_indent_symbol: Symbol for the base indentation

        Raises:
            ValidationError: If the provided level is invalid
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        self._level = level.upper()
        self._indent = 0
        self._indent_step = indent_step
        self._indent_symbol = indent_symbol
        self._base_indent_symbol = base_indent_symbol

        # Initialiser Rich Console
        self._console = Console()
        self._level_numeric = LogLevel.get_no(self._level)

        # Initialiser Rich Wizard pour fonctionnalités avancées
        self._wizard = RichWizard(self._console)

        # Wrapper pour compatibilité API
        self._wrapper = ConsolePrinterWrapper(self)

    # ///////////////////////////////////////////////////////////////
    # GETTER
    # ///////////////////////////////////////////////////////////////

    def get_printer(self) -> ConsolePrinterWrapper:
        """
        Get a wrapper object compatible with the existing API.

        Returns:
            ConsolePrinterWrapper instance that provides info(), debug(), etc.
        """
        return self._wrapper

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
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        self._level = level.upper()
        self._level_numeric = LogLevel.get_no(self._level)

    def log(self, level: str, message: Any) -> None:
        """
        Log a message with the specified level.

        Args:
            level: The log level
            message: The message to log (any type, will be safely converted to string)

        Raises:
            ValidationError: If the level is invalid
        """
        if not LogLevel.is_valid_level(level):
            raise ValidationError(f"Invalid log level: {level}", "level", level)

        # Convertir message en string de manière robuste
        message = safe_str_convert(message)
        message = sanitize_for_console(message)

        try:
            level_numeric = LogLevel.get_no(level)
            if level_numeric < self._level_numeric:
                return  # Niveau trop bas, ne pas afficher

            # Map log levels to patterns for consistent output
            pattern_map = {
                "DEBUG": Pattern.DEBUG,
                "INFO": Pattern.INFO,
                "SUCCESS": Pattern.SUCCESS,
                "WARNING": Pattern.WARN,
                "ERROR": Pattern.ERROR,
                "CRITICAL": Pattern.ERROR,  # Critical also uses ERROR pattern
            }
            pattern_enum = pattern_map.get(level.upper(), Pattern.INFO)
            self.print_pattern(pattern_enum, message, level)

        except Exception as e:
            # Ne pas lever d'exception, juste logger l'erreur de manière sécurisée
            try:
                self._console.print(
                    f"[bold red]LOGGING ERROR:[/bold red] {type(e).__name__}"
                )
            except Exception as e:
                raise ValueError(f"Failed to print logging error: {e}") from e

    # ///////////////////////////////////////////////////////////////
    # LOGGING METHODS (API primaire)
    # ///////////////////////////////////////////////////////////////

    def info(self, message: Any) -> None:
        """Log an informational message with pattern format."""
        self.print_pattern(Pattern.INFO, message, "INFO")

    def debug(self, message: Any) -> None:
        """Log a debug message with pattern format."""
        self.print_pattern(Pattern.DEBUG, message, "DEBUG")

    def success(self, message: Any) -> None:
        """Log a success message with pattern format."""
        self.print_pattern(Pattern.SUCCESS, message, "INFO")

    def warning(self, message: Any) -> None:
        """Log a warning message with pattern format."""
        self.print_pattern(Pattern.WARN, message, "WARNING")

    def warn(self, message: Any) -> None:
        """Log a warning message with pattern format (alias for warning)."""
        self.warning(message)

    def error(self, message: Any) -> None:
        """Log an error message with pattern format."""
        self.print_pattern(Pattern.ERROR, message, "ERROR")

    def critical(self, message: Any) -> None:
        """Log a critical message with pattern format."""
        self.print_pattern(Pattern.ERROR, message, "CRITICAL")

    # ------------------------------------------------
    # ADDITIONAL PATTERN METHODS
    # ------------------------------------------------

    def tip(self, message: Any) -> None:
        """Display a tip message with pattern format."""
        self.print_pattern(Pattern.TIP, message, "INFO")

    def system(self, message: Any) -> None:
        """Display a system message with pattern format."""
        self.print_pattern(Pattern.SYSTEM, message, "INFO")

    def install(self, message: Any) -> None:
        """Display an installation message with pattern format."""
        self.print_pattern(Pattern.INSTALL, message, "INFO")

    def detect(self, message: Any) -> None:
        """Display a detection message with pattern format."""
        self.print_pattern(Pattern.DETECT, message, "INFO")

    def config(self, message: Any) -> None:
        """Display a configuration message with pattern format."""
        self.print_pattern(Pattern.CONFIG, message, "INFO")

    def deps(self, message: Any) -> None:
        """Display a dependencies message with pattern format."""
        self.print_pattern(Pattern.DEPS, message, "INFO")

    def print_pattern(
        self, pattern: Union[str, Pattern], message: Any, level: str = "INFO"
    ) -> None:
        """
        Display a message with pattern format: • PATTERN :: message

        Args:
            pattern: Pattern name (string) or Pattern enum
            message: Message to display
            level: Log level for filtering (default: INFO)
        """
        try:
            # Convert pattern to Pattern enum if string
            if isinstance(pattern, str):
                try:
                    pattern_enum = Pattern[pattern.upper()]
                except KeyError:
                    # If pattern not found, use INFO as default
                    pattern_enum = Pattern.INFO
            else:
                pattern_enum = pattern

            # Check if level should be displayed
            level_numeric = LogLevel.get_no(level)
            if level_numeric < self._level_numeric:
                return  # Level too low, don't display

            # Convert message to string safely and sanitize for console
            message = safe_str_convert(message)
            message = sanitize_for_console(message)

            # Get pattern color
            pattern_color = get_pattern_color(pattern_enum)
            pattern_name = pattern_enum.value

            # Build text with pattern format: • PATTERN :: message
            text = Text()
            text.append("• ", style=pattern_color)
            text.append(pattern_name.ljust(8), style=f"bold {pattern_color}")
            text.append(":: ", style="dim white")

            # Handle indentation - add it just before the message (after ":: ")
            indent_str = self.get_indent()
            if indent_str and indent_str != "~":
                # Add indentation just before the message
                text.append(indent_str, style="dim")
                text.append(" ", style="dim")

            # Add the message
            text.append(str(message), style="white")

            self._console.print(text)

        except Exception as e:
            # Robust error handling: never raise exception
            try:
                error_msg = f"[bold red]PATTERN ERROR:[/bold red] {type(e).__name__}"
                self._console.print(error_msg)
            except Exception as e:
                raise ValueError(f"Failed to print pattern: {e}") from e

    # ///////////////////////////////////////////////////////////////
    # INDENTATION MANAGEMENT
    # ///////////////////////////////////////////////////////////////

    def get_indent(self) -> str:
        """
        Get the current indentation string.

        Returns:
            The current indentation string
        """
        try:
            indent_spaces = " " * (self._indent * self._indent_step)
            if self._indent > 0:
                return f"{indent_spaces}{self._indent_symbol}"
            else:
                return self._base_indent_symbol
        except Exception:
            return "~"  # Fallback sécurisé

    def add_indent(self) -> None:
        """Increase the indentation level by one (with maximum limit)."""
        self._indent = min(self._indent + 1, self.MAX_INDENT)

    def del_indent(self) -> None:
        """Decrease the indentation level by one, ensuring it doesn't go below zero."""
        self._indent = max(0, self._indent - 1)

    def reset_indent(self) -> None:
        """Reset the indentation level to zero."""
        self._indent = 0

    @contextmanager
    def manage_indent(self) -> Generator[None, None, None]:
        """
        Context manager for temporary indentation.

        Yields:
            None
        """
        try:
            self.add_indent()
            yield
        finally:
            self.del_indent()

    # ///////////////////////////////////////////////////////////////
    # ENHANCED METHODS (Rich features)
    # ///////////////////////////////////////////////////////////////

    def print_table(
        self, data: list[dict[str, Any]], title: Optional[str] = None
    ) -> None:
        """
        Display a table using Rich (delegates to RichWizard).

        Args:
            data: List of dictionaries representing table rows
            title: Optional table title
        """
        self._wizard.table(data, title=title)

    def print_panel(
        self, content: str, title: Optional[str] = None, style: str = "blue"
    ) -> None:
        """
        Display a panel using Rich (delegates to RichWizard).

        Args:
            content: Panel content
            title: Optional panel title
            style: Panel style (Rich style string, used as border_style)
        """
        self._wizard.panel(content, title=title, border_style=style)

    def print_progress(self, *args, **kwargs) -> None:
        """
        Display a progress bar using Rich.

        Note: This is a placeholder. For full progress functionality,
        users should use Rich's Progress context manager directly.
        """
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                *args,
                **kwargs,
            ):
                # Placeholder - les utilisateurs devraient utiliser Rich.Progress directement
                pass
        except Exception as e:
            try:
                self._console.print(f"[red]Progress error:[/red] {type(e).__name__}")
            except Exception as e:
                raise ValueError(f"Failed to print progress: {e}") from e

    def print_json(
        self,
        data: Union[str, dict, list],
        title: Optional[str] = None,
        indent: Optional[int] = None,
        highlight: bool = True,
    ) -> None:
        """
        Display JSON data in a formatted and syntax-highlighted way using Rich (delegates to RichWizard).

        Args:
            data: JSON data to display (dict, list, or JSON string)
            title: Optional title for the JSON display
            indent: Number of spaces for indentation (default: 2)
            highlight: Whether to enable syntax highlighting (default: True)

        Examples:
            >>> printer.print_json({"name": "Alice", "age": 30})
            >>> printer.print_json('{"key": "value"}', title="Config")
            >>> printer.print_json([1, 2, 3], indent=4)
        """
        self._wizard.json(data, title=title, indent=indent, highlight=highlight)

    # ///////////////////////////////////////////////////////////////
    # REPRESENTATION METHODS
    # ///////////////////////////////////////////////////////////////

    def __str__(self) -> str:
        """String representation of the console printer."""
        return f"ConsolePrinter(level={self._level}, indent={self._indent})"

    def __repr__(self) -> str:
        """Detailed string representation of the console printer."""
        return f"ConsolePrinter(level={self._level}, indent={self._indent}, indent_step={self._indent_step})"
