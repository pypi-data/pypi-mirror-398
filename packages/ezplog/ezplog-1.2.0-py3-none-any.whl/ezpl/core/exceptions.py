# ///////////////////////////////////////////////////////////////
# EZPL - Core Exceptions
# Project: ezpl
# ///////////////////////////////////////////////////////////////

"""
Core exceptions for Ezpl logging framework.

This module defines all custom exceptions used throughout the application.
"""

## ==> CLASSES
# ///////////////////////////////////////////////////////////////


class EzplError(Exception):
    """
    Base exception class for all Ezpl-related errors.

    This is the base class for all exceptions raised by the Ezpl framework.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, message: str, error_code: str = None) -> None:
        """
        Initialize the Ezpl error.

        Args:
            message: Error message
            error_code: Optional error code for categorization
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    # ///////////////////////////////////////////////////////////////
    # REPRESENTATION METHODS
    # ///////////////////////////////////////////////////////////////

    def __str__(self) -> str:
        """String representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationError(EzplError):
    """
    Exception raised for configuration-related errors.

    This exception is raised when there are issues with configuration
    loading, validation, or processing.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, message: str, config_key: str = None) -> None:
        """
        Initialize the configuration error.

        Args:
            message: Error message
            config_key: Optional configuration key that caused the error
        """
        super().__init__(message, "CONFIG_ERROR")
        self.config_key = config_key


class LoggingError(EzplError):
    """
    Exception raised for logging-related errors.

    This exception is raised when there are issues with logging operations,
    such as file writing, formatting, or handler initialization.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, message: str, handler_type: str = None) -> None:
        """
        Initialize the logging error.

        Args:
            message: Error message
            handler_type: Optional handler type that caused the error
        """
        super().__init__(message, "LOGGING_ERROR")
        self.handler_type = handler_type


class ValidationError(EzplError):
    """
    Exception raised for validation errors.

    This exception is raised when input validation fails,
    such as invalid log levels or malformed configuration values.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, message: str, field_name: str = None, value: str = None) -> None:
        """
        Initialize the validation error.

        Args:
            message: Error message
            field_name: Optional field name that failed validation
            value: Optional value that failed validation
        """
        super().__init__(message, "VALIDATION_ERROR")
        self.field_name = field_name
        self.value = value


class InitializationError(EzplError):
    """
    Exception raised for initialization errors.

    This exception is raised when there are issues during the
    initialization of Ezpl components.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, message: str, component: str = None) -> None:
        """
        Initialize the initialization error.

        Args:
            message: Error message
            component: Optional component that failed to initialize
        """
        super().__init__(message, "INIT_ERROR")
        self.component = component


class FileOperationError(EzplError):
    """
    Exception raised for file operation errors.

    This exception is raised when there are issues with file operations,
    such as reading, writing, or creating files.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self, message: str, file_path: str = None, operation: str = None
    ) -> None:
        """
        Initialize the file operation error.

        Args:
            message: Error message
            file_path: Optional file path that caused the error
            operation: Optional operation that failed
        """
        super().__init__(message, "FILE_ERROR")
        self.file_path = file_path
        self.operation = operation


class HandlerError(EzplError):
    """
    Exception raised for handler-related errors.

    This exception is raised when there are issues with logging handlers,
    such as initialization, configuration, or operation failures.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, message: str, handler_name: str = None) -> None:
        """
        Initialize the handler error.

        Args:
            message: Error message
            handler_name: Optional handler name that caused the error
        """
        super().__init__(message, "HANDLER_ERROR")
        self.handler_name = handler_name
