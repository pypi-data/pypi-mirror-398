"""Base response class for EchoIntel SDK."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

T = TypeVar("T", bound="EchoIntelResponse")


class EchoIntelResponse(ABC):
    """Abstract base class for all EchoIntel API responses.

    Provides common functionality for response hydration, serialization,
    and dict-like access to the underlying data.
    """

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        """Initialize the response with raw API data.

        Args:
            data: Raw response data from the API.
        """
        self._data = data or {}
        self._hydrate(self._data)

    @abstractmethod
    def _hydrate(self, data: dict[str, Any]) -> None:
        """Populate typed attributes from raw API data.

        Args:
            data: Raw response data from the API.
        """

    def to_dict(self) -> dict[str, Any]:
        """Convert the response to a dictionary.

        Returns:
            Original API response data.
        """
        return self._data

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """Create a response instance from a dictionary.

        Args:
            data: Raw response data from the API.

        Returns:
            New instance of the response class.
        """
        return cls(data)

    def __getitem__(self, key: str) -> Any:
        """Get an item from the underlying data."""
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an item in the underlying data."""
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the underlying data."""
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        """Get an item from the underlying data with a default.

        Args:
            key: The key to look up.
            default: Default value if key is not found.

        Returns:
            The value for the key or the default.
        """
        return self._data.get(key, default)
