"""Blizzard API exceptions."""

from .auth import AuthenticationError, InvalidCredentialsError, TokenError, TokenExpiredError
from .base import BlizzardAPIError
from .request import BadRequestError, ForbiddenError, NotFoundError, RateLimitError, RequestError, ServerError
from .validation import InvalidLocaleError, InvalidRegionError, MissingParameterError, ValidationError

__all__ = [
    # Base
    "BlizzardAPIError",
    # Auth
    "AuthenticationError",
    "TokenError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    # Request
    "RequestError",
    "RateLimitError",
    "NotFoundError",
    "ServerError",
    "BadRequestError",
    "ForbiddenError",
    # Validation
    "ValidationError",
    "InvalidRegionError",
    "InvalidLocaleError",
    "MissingParameterError",
]
