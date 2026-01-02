"""Authentication-related exceptions."""

from dataclasses import dataclass

from .base import BlizzardAPIError


@dataclass(slots=True)
class AuthenticationError(BlizzardAPIError):
    """Base class for authentication errors."""

    pass


@dataclass(slots=True)
class TokenError(AuthenticationError):
    """OAuth token error.

    Attributes:
        token_type: Type of token (e.g., "bearer")
        expires_in: Token expiration time in seconds
    """

    token_type: str | None = None
    expires_in: int | None = None

    def __str__(self) -> str:
        """Format token error message."""
        parts = [f"TokenError: {self.message}"]

        if self.status_code:
            parts.append(f"Status: {self.status_code}")

        if self.token_type:
            parts.append(f"Token Type: {self.token_type}")

        return " | ".join(parts)


@dataclass(slots=True)
class InvalidCredentialsError(AuthenticationError):
    """Invalid client credentials provided."""

    pass


@dataclass(slots=True)
class TokenExpiredError(AuthenticationError):
    """Access token has expired.

    Attributes:
        expired_at: Unix timestamp when token expired
    """

    expired_at: int | None = None

    def __str__(self) -> str:
        """Format token expiration error."""
        parts = [f"TokenExpiredError: {self.message}"]

        if self.expired_at:
            parts.append(f"Expired at: {self.expired_at}")

        return " | ".join(parts)
