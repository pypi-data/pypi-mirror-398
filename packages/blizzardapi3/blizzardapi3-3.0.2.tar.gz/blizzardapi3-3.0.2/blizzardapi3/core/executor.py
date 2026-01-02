"""HTTP request executor with retry logic and error handling."""

from typing import Any

import aiohttp
import requests

from ..exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RequestError,
    ServerError,
)
from .auth import TokenManager
from .context import RequestContext


class RequestExecutor:
    """Executes HTTP requests to Blizzard API with error handling.

    Handles token management, retries, and converts HTTP errors
    to appropriate exception types.
    """

    BASE_URL = "https://{region}.api.blizzard.com"
    MAX_RETRIES = 1

    def __init__(self, token_manager: TokenManager):
        """Initialize request executor.

        Args:
            token_manager: Token manager for OAuth authentication
        """
        self.token_manager = token_manager

    def execute(self, context: RequestContext, session: requests.Session) -> dict[str, Any]:
        """Execute synchronous API request.

        Args:
            context: Request context with path, params, etc.
            session: requests Session to use

        Returns:
            API response data as dictionary

        Raises:
            NotFoundError: Resource not found (404)
            RateLimitError: Rate limit exceeded (429)
            ServerError: Server error (5xx)
            RequestError: Other request errors
        """
        # Get access token
        if context.access_token:
            token = context.access_token
        else:
            token = self.token_manager.get_token(context.region, session)

        # Build URL
        url = f"{self.BASE_URL.format(region=context.region)}{context.path}"

        # Prepare params and headers
        params = context.query_params
        headers = {"Authorization": f"Bearer {token}"}

        # Execute with retry logic
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = session.get(url, params=params, headers=headers, timeout=30)

                if response.status_code == 200:
                    return response.json()

                # Handle 401 - token might be invalid, retry once
                if response.status_code == 401 and attempt < self.MAX_RETRIES and not context.access_token:
                    self.token_manager.invalidate()
                    token = self.token_manager.get_token(context.region, session)
                    headers["Authorization"] = f"Bearer {token}"
                    continue

                # Handle other errors
                self._handle_error_response(response, url)

            except requests.RequestException as e:
                raise RequestError(f"Request failed: {str(e)}", request_url=url)

        raise RequestError("Max retries exceeded", request_url=url)

    async def execute_async(self, context: RequestContext, session: aiohttp.ClientSession) -> dict[str, Any]:
        """Execute asynchronous API request.

        Args:
            context: Request context with path, params, etc.
            session: aiohttp ClientSession to use

        Returns:
            API response data as dictionary

        Raises:
            NotFoundError: Resource not found (404)
            RateLimitError: Rate limit exceeded (429)
            ServerError: Server error (5xx)
            RequestError: Other request errors
        """
        # Get access token
        if context.access_token:
            token = context.access_token
        else:
            token = await self.token_manager.get_token_async(context.region, session)

        # Build URL
        url = f"{self.BASE_URL.format(region=context.region)}{context.path}"

        # Prepare params and headers
        params = context.query_params
        headers = {"Authorization": f"Bearer {token}"}

        # Execute with retry logic
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                async with session.get(
                    url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status == 200:
                        return await response.json()

                    # Handle 401 - token might be invalid, retry once
                    if response.status == 401 and attempt < self.MAX_RETRIES and not context.access_token:
                        self.token_manager.invalidate()
                        token = await self.token_manager.get_token_async(context.region, session)
                        headers["Authorization"] = f"Bearer {token}"
                        continue

                    # Handle other errors
                    await self._handle_error_response_async(response, url)

            except aiohttp.ClientError as e:
                raise RequestError(f"Request failed: {str(e)}", request_url=url)

        raise RequestError("Max retries exceeded", request_url=url)

    def _handle_error_response(self, response: requests.Response, url: str) -> None:
        """Handle HTTP error responses (synchronous).

        Args:
            response: HTTP response object
            url: Request URL

        Raises:
            Appropriate exception based on status code
        """
        error_data = None
        try:
            error_data = response.json()
        except Exception:
            pass

        status_code = response.status_code

        if status_code == 400:
            raise BadRequestError(
                "Bad request - invalid parameters", status_code=400, request_url=url, response_data=error_data
            )

        if status_code == 403:
            raise ForbiddenError(
                "Forbidden - insufficient permissions",
                status_code=403,
                request_url=url,
                response_data=error_data,
            )

        if status_code == 404:
            raise NotFoundError("Resource not found", status_code=404, request_url=url, response_data=error_data)

        if status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                "Rate limit exceeded",
                status_code=429,
                request_url=url,
                retry_after=int(retry_after) if retry_after else None,
                response_data=error_data,
            )

        if 500 <= status_code < 600:
            raise ServerError(
                f"Server error: {status_code}", status_code=status_code, request_url=url, response_data=error_data
            )

        raise RequestError(
            f"Request failed: {status_code}", status_code=status_code, request_url=url, response_data=error_data
        )

    async def _handle_error_response_async(self, response: aiohttp.ClientResponse, url: str) -> None:
        """Handle HTTP error responses (asynchronous).

        Args:
            response: HTTP response object
            url: Request URL

        Raises:
            Appropriate exception based on status code
        """
        error_data = None
        try:
            if response.content_type == "application/json":
                error_data = await response.json()
        except Exception:
            pass

        status_code = response.status

        if status_code == 400:
            raise BadRequestError(
                "Bad request - invalid parameters", status_code=400, request_url=url, response_data=error_data
            )

        if status_code == 403:
            raise ForbiddenError(
                "Forbidden - insufficient permissions",
                status_code=403,
                request_url=url,
                response_data=error_data,
            )

        if status_code == 404:
            raise NotFoundError("Resource not found", status_code=404, request_url=url, response_data=error_data)

        if status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                "Rate limit exceeded",
                status_code=429,
                request_url=url,
                retry_after=int(retry_after) if retry_after else None,
                response_data=error_data,
            )

        if 500 <= status_code < 600:
            raise ServerError(
                f"Server error: {status_code}", status_code=status_code, request_url=url, response_data=error_data
            )

        raise RequestError(
            f"Request failed: {status_code}", status_code=status_code, request_url=url, response_data=error_data
        )
