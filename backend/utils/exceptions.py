"""
Custom Exception Classes
Provides specific exceptions for better error handling.
"""


class NIREException(Exception):
    """Base exception for all NIRE errors."""
    pass


class ModelLoadError(NIREException):
    """Raised when LLM model fails to load."""
    pass


class InferenceError(NIREException):
    """Raised when LLM inference fails."""
    pass


class MemoryError(NIREException):
    """Raised when memory operations fail."""
    pass


class DatabaseConnectionError(NIREException):
    """Raised when database connection fails."""
    pass


class ConfigurationError(NIREException):
    """Raised when configuration is invalid."""
    pass
