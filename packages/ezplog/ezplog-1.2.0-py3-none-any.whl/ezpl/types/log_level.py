# ///////////////////////////////////////////////////////////////
# EZPL - LogLevel enumeration
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
LogLevel enumeration for Ezpl logging framework.

This module defines the logging levels with their associated colors and properties.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
from enum import Enum
from typing import Any

# External libraries
from loguru import logger

# Internal modules
from ..core.exceptions import ValidationError

## ==> CLASSES
# ///////////////////////////////////////////////////////////////


class LogLevel(Enum):
    """
    LogLevel is an enumeration representing different logging levels with associated names,
    numeric levels, and colorimetric configurations.

    **Attributes:**
        * `label`: Human-readable name of the log level
        * `no`: Numeric level for comparison
        * `fg`: Foreground color code
        * `bg`: Background color code

    **Levels:**
        * `DEBUG`: Debugging messages (lowest priority)
        * `INFO`: Informational messages
        * `SUCCESS`: Success messages
        * `WARNING`: Warning messages
        * `ERROR`: Error messages
        * `CRITICAL`: Critical messages (highest priority)
    """

    DEBUG = (
        logger.level("DEBUG").name,
        logger.level("DEBUG").no,
        "e",  # cyan
        "K",  # black
    )
    INFO = (
        logger.level("INFO").name,
        logger.level("INFO").no,
        "w",  # white
        "K",  # black
    )
    SUCCESS = (
        logger.level("SUCCESS").name,
        logger.level("SUCCESS").no,
        "w",  # white
        "G",  # green
    )
    WARNING = (
        logger.level("WARNING").name,
        logger.level("WARNING").no,
        "y",  # yellow
        "K",  # black
    )
    ERROR = (
        logger.level("ERROR").name,
        logger.level("ERROR").no,
        "r",  # red
        "K",  # black
    )
    CRITICAL = (
        logger.level("CRITICAL").name,
        logger.level("CRITICAL").no,
        "w",  # white
        "M",  # magenta
    )

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    label: str
    no: int
    fg: str
    bg: str

    def __init__(self, label: str, no: int, fg: str, bg: str) -> None:
        """
        Initialize a LogLevel instance.

        Args:
            label: Human-readable name of the log level
            no: Numeric level for comparison
            fg: Foreground color code
            bg: Background color code
        """
        self.label = label
        self.no = no
        self.fg = fg
        self.bg = bg

    # ///////////////////////////////////////////////////////////////
    # CLASS METHODS
    # ///////////////////////////////////////////////////////////////

    @classmethod
    def get_attribute(cls, level: str, attribute: str) -> Any:
        """
        Returns the specified attribute (label, no, fg, bg) for a given logging level.

        Args:
            level: The logging level name
            attribute: The attribute to retrieve ('label', 'no', 'fg', 'bg')

        Returns:
            The requested attribute value

        Raises:
            ValueError: If the level or attribute is not found
        """
        try:
            lvl = cls[level.upper()]
            return getattr(lvl, attribute)
        except KeyError as e:
            raise ValidationError(f"Unknown level '{level}'", "level", level) from e
        except AttributeError as e:
            raise ValidationError(
                f"Invalid attribute '{attribute}'", "attribute", attribute
            ) from e

    @classmethod
    def get_label(cls, level: str) -> str:
        """
        Get the label for a given log level.

        Args:
            level: The logging level name

        Returns:
            The label for the log level
        """
        return cls.get_attribute(level, "label")

    @classmethod
    def get_no(cls, level: str) -> int:
        """
        Get the numeric level for a given log level.

        Args:
            level: The logging level name

        Returns:
            The numeric level
        """
        return cls.get_attribute(level, "no")

    @classmethod
    def get_fgcolor(cls, level: str) -> str:
        """
        Get the foreground color for a given log level.

        Args:
            level: The logging level name

        Returns:
            The foreground color code
        """
        return cls.get_attribute(level, "fg")

    @classmethod
    def get_bgcolor(cls, level: str) -> str:
        """
        Get the background color for a given log level.

        Args:
            level: The logging level name

        Returns:
            The background color code
        """
        return cls.get_attribute(level, "bg")

    @classmethod
    def is_valid_level(cls, level: str) -> bool:
        """
        Check if a given level is valid.

        Args:
            level: The logging level name to check

        Returns:
            True if the level is valid, False otherwise
        """
        try:
            cls[level.upper()]
            return True
        except KeyError:
            return False

    @classmethod
    def get_all_levels(cls) -> list[str]:
        """
        Get all available log levels.

        Returns:
            List of all available log level names
        """
        return [level.name for level in cls]

    # ///////////////////////////////////////////////////////////////
    # REPRESENTATION METHODS
    # ///////////////////////////////////////////////////////////////

    def __str__(self) -> str:
        """String representation of the log level."""
        return f"LogLevel.{self.name}({self.label})"

    def __repr__(self) -> str:
        """Detailed string representation of the log level."""
        return f"LogLevel.{self.name}(label='{self.label}', no={self.no}, fg='{self.fg}', bg='{self.bg}')"

    def get_rich_style(self) -> str:
        """
        Get the Rich style string for this log level.

        Returns:
            Rich style string (e.g., "bold red", "cyan", etc.)
        """
        styles = {
            "DEBUG": "cyan",
            "INFO": "blue",
            "SUCCESS": "bold green",
            "WARNING": "bold yellow",
            "ERROR": "bold red",
            "CRITICAL": "bold magenta on red",
        }
        return styles.get(self.name, "")
