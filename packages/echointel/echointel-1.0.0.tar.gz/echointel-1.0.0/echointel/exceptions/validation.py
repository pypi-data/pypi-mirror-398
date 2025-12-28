"""Validation exception for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.exceptions.base import EchoIntelException


class EchoIntelValidationException(EchoIntelException):
    """Exception raised when request validation fails.

    This exception is raised for HTTP 422 (Unprocessable Entity)
    responses from the API, typically containing validation errors.

    Attributes:
        errors: Dictionary of field-level validation errors.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        errors: dict[str, list[str]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the validation exception.

        Args:
            message: The error message.
            errors: Dictionary of field-level validation errors.
            context: Additional context data about the error.
        """
        super().__init__(message=message, status_code=422, context=context)
        self.errors = errors or {}

    def get_errors(self) -> dict[str, list[str]]:
        """Get the validation errors.

        Returns:
            Dictionary mapping field names to lists of error messages.
        """
        return self.errors

    def get_first_error(self, field: str | None = None) -> str | None:
        """Get the first error message for a field or overall.

        Args:
            field: Optional field name to get error for.

        Returns:
            First error message or None if no errors.
        """
        if field:
            field_errors = self.errors.get(field, [])
            return field_errors[0] if field_errors else None

        for field_errors in self.errors.values():
            if field_errors:
                return field_errors[0]
        return None

    def __str__(self) -> str:
        """Return string representation of the exception."""
        if self.errors:
            error_count = sum(len(errs) for errs in self.errors.values())
            return f"[422] {self.message} ({error_count} validation error(s))"
        return f"[422] {self.message}"
