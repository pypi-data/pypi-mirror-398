"""Base error classes for Konic."""

__all__ = ["KonicError"]


class KonicError(Exception):
    """
    Base exception class for all Konic-specific errors.

    This class serves as a unified error type that inherits from multiple
    exception types to maintain compatibility with existing code while
    providing a single exception type for the Konic framework.
    """

    def __init__(self, message: str, *args):
        """
        Initialize the KonicError.

        Args:
            message: The error message
            *args: Additional arguments passed to the parent exception classes
        """
        super().__init__(message, *args)
        self.message = message


class KonicAssertionError(AssertionError):
    """Konic-specific AssertionError subclass used to indicate assertion failures"""

    pass
