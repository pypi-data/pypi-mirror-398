"""HTTP request-related exceptions."""

from dataclasses import dataclass
from typing import Any

from .base import BlizzardAPIError


@dataclass(slots=True)
class RequestError(BlizzardAPIError):
    """Base class for HTTP request errors.

    Attributes:
        retry_after: Seconds to wait before retrying (from Retry-After header)
        error_code: API-specific error code
        error_details: Additional error details from API
    """

    retry_after: int | None = None
    error_code: str | None = None
    error_details: dict[str, Any] | None = None

    @property
    def is_rate_limited(self) -> bool:
        """Check if error is due to rate limiting."""
        return self.status_code == 429 or self.retry_after is not None

    @property
    def should_retry(self) -> bool:
        """Check if request should be retried."""
        if self.is_rate_limited:
            return True
        return self.status_code in (500, 502, 503, 504) if self.status_code else False


@dataclass(slots=True)
class RateLimitError(RequestError):
    """API rate limit exceeded (429).

    The client has sent too many requests in a given timeframe.
    """

    def __str__(self) -> str:
        """Format rate limit error message."""
        msg = f"RateLimitError: {self.message}"
        if self.retry_after:
            msg += f" | Retry after {self.retry_after} seconds"
        return msg


@dataclass(slots=True)
class NotFoundError(RequestError):
    """Resource not found (404).

    The requested resource does not exist.
    """

    pass


@dataclass(slots=True)
class ServerError(RequestError):
    """Server error (5xx).

    The API server encountered an error processing the request.
    """

    pass


@dataclass(slots=True)
class BadRequestError(RequestError):
    """Bad request (400).

    The request was malformed or contained invalid parameters.
    """

    pass


@dataclass(slots=True)
class ForbiddenError(RequestError):
    """Forbidden (403).

    The request was valid but the server is refusing to respond.
    Insufficient permissions or scope.
    """

    pass
