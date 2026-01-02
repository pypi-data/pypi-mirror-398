"""Request context for API calls."""

from dataclasses import dataclass
from typing import Any


@dataclass
class RequestContext:
    """Context information for an API request.

    Attributes:
        region: API region (e.g., "us", "eu")
        path: API endpoint path
        query_params: Query string parameters
        access_token: User-provided OAuth access token (optional)
        auth_type: Type of authentication ("client_credentials" or "oauth")
    """

    region: str
    path: str
    query_params: dict[str, Any]
    access_token: str | None = None
    auth_type: str = "client_credentials"
