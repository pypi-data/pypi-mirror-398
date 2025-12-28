"""Base exception for EchoIntel SDK."""

from __future__ import annotations

from typing import Any


class EchoIntelException(Exception):
    """Base exception for all EchoIntel SDK errors.

    Attributes:
        message: The error message.
        status_code: HTTP status code if applicable.
        context: Additional context data about the error.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            status_code: HTTP status code if applicable.
            context: Additional context data about the error.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.context = context or {}

    def __str__(self) -> str:
        """Return string representation of the exception."""
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        """Return detailed representation of the exception."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r}, "
            f"context={self.context!r})"
        )
