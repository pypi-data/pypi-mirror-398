"""Base exception for all Blizzard API errors."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class BlizzardAPIError(Exception):
    """Base exception for all Blizzard API errors.

    Attributes:
        message: Error message describing what went wrong
        status_code: HTTP status code if applicable
        request_url: The URL that was requested
        response_data: Raw response data from the API if available
    """

    message: str
    status_code: int | None = None
    request_url: str | None = None
    response_data: dict[str, Any] | None = None

    def __str__(self) -> str:
        """Format error message with context."""
        parts = [f"BlizzardAPIError: {self.message}"]

        if self.status_code:
            parts.append(f"Status: {self.status_code}")

        if self.request_url:
            parts.append(f"URL: {self.request_url}")

        return " | ".join(parts)
