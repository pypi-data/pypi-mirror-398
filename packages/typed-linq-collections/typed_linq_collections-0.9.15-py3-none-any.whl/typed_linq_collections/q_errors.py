from __future__ import annotations


class InvalidOperationError(Exception):
    """Raised when a method call is invalid for the object's current state."""
    def __init__(self, message: str = "The called method cannot be called with the object in the current state") -> None:
        super().__init__(message)

class EmptyIterableError(InvalidOperationError):
    """Raised when an operation is attempted on an empty Iterable."""
    def __init__(self) -> None:
        super().__init__("The operation cannot be performed on an empty Iterable.")

class ArgumentError(ValueError):
    """Raised when an argument is invalid."""
    def __init__(self, message: str = "The argument is invalid.") -> None:
        super().__init__(message)