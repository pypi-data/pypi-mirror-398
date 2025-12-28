"""Authentication exception for EchoIntel SDK."""

from __future__ import annotations

from echointel.exceptions.base import EchoIntelException


class EchoIntelAuthenticationException(EchoIntelException):
    """Exception raised when authentication fails.

    This exception is raised for HTTP 401 (Unauthorized) and
    HTTP 403 (Forbidden) responses from the API.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int = 401,
    ) -> None:
        """Initialize the authentication exception.

        Args:
            message: The error message.
            status_code: HTTP status code (401 or 403).
        """
        super().__init__(message=message, status_code=status_code)
