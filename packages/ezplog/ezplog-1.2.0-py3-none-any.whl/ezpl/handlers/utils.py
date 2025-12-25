# ///////////////////////////////////////////////////////////////
# EZPL - Handler Utilities
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Utility functions for message handling in handlers.

This module provides robust message conversion and sanitization functions.
"""

# IMPORTS
# ///////////////////////////////////////////////////////////////
# Base imports
import re
from typing import Any

## ==> FUNCTIONS
# ///////////////////////////////////////////////////////////////


def safe_str_convert(obj: Any) -> str:
    """
    Safely convert any object to string with multiple fallback strategies.

    Args:
        obj: Object to convert to string

    Returns:
        String representation of the object (never fails)
    """
    if obj is None:
        return "None"

    if isinstance(obj, str):
        return obj

    # Try str() first (most common case)
    try:
        return str(obj)
    except Exception as e:
        raise ValueError(f"Failed to convert object to string: {obj}") from e

    # Fallback to repr() if str() fails
    try:
        return repr(obj)
    except Exception as e:
        raise ValueError(f"Failed to convert object to string: {obj}") from e

    # Last resort: type name
    try:
        return f"<{type(obj).__name__} object>"
    except Exception as e:
        raise ValueError(f"Failed to convert object to string: {obj}") from e


def sanitize_for_file(message: str) -> str:
    """
    Sanitize a message for file output by removing problematic characters.

    Args:
        message: Message to sanitize

    Returns:
        Sanitized message safe for file output
    """
    if not isinstance(message, str):
        message = safe_str_convert(message)

    # Remove null bytes and other control characters (except newlines and tabs)
    message = re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]", "", message)

    # Remove ANSI escape sequences
    message = re.sub(r"\x1B\[[0-9;]*[a-zA-Z]", "", message)

    # Remove HTML/loguru tags more aggressively
    message = re.sub(r"</?>", "", message)  # Remove all < and >
    message = re.sub(r"<[^>]+>", "", message)  # Remove any remaining tags

    # Replace problematic characters that might break file encoding
    # Keep Unicode characters but ensure they're valid
    try:
        message.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        # Replace problematic Unicode characters
        message = message.encode("utf-8", errors="replace").decode("utf-8")

    return message


def sanitize_for_console(message: str) -> str:
    """
    Sanitize a message for console output (less aggressive, Rich handles most cases).

    Args:
        message: Message to sanitize

    Returns:
        Sanitized message safe for console output
    """
    if not isinstance(message, str):
        message = safe_str_convert(message)

    # Remove null bytes (Rich can handle most other characters)
    message = message.replace("\x00", "")

    # Remove other control characters that might break terminal
    message = re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]", "", message)

    return message
