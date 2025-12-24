"""OAuth token management."""

import time

import aiohttp
import requests

from ..exceptions import TokenError


class TokenManager:
    """Manages OAuth token lifecycle with automatic refresh.

    Attributes:
        TOKEN_BUFFER_SECONDS: Refresh tokens 5 minutes before expiry
    """

    TOKEN_BUFFER_SECONDS = 300  # 5 minutes

    def __init__(self, client_id: str, client_secret: str):
        """Initialize token manager.

        Args:
            client_id: Blizzard API client ID
            client_secret: Blizzard API client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret

        self._token: str | None = None
        self._token_type: str | None = None
        self._expires_at: float | None = None

    def is_token_valid(self) -> bool:
        """Check if current token is valid.

        Returns:
            True if token exists and hasn't expired (with buffer)
        """
        if not self._token or not self._expires_at:
            return False
        return time.time() < (self._expires_at - self.TOKEN_BUFFER_SECONDS)

    def get_token(self, region: str, session: requests.Session) -> str:
        """Get valid access token (synchronous).

        Args:
            region: API region for OAuth endpoint
            session: requests Session to use

        Returns:
            Valid access token

        Raises:
            TokenError: If token fetch fails
        """
        if self.is_token_valid():
            return self._token

        return self._fetch_token(region, session)

    async def get_token_async(self, region: str, session: aiohttp.ClientSession) -> str:
        """Get valid access token (asynchronous).

        Args:
            region: API region for OAuth endpoint
            session: aiohttp ClientSession to use

        Returns:
            Valid access token

        Raises:
            TokenError: If token fetch fails
        """
        if self.is_token_valid():
            return self._token

        return await self._fetch_token_async(region, session)

    def _fetch_token(self, region: str, session: requests.Session) -> str:
        """Fetch new access token (synchronous).

        Args:
            region: API region for OAuth endpoint
            session: requests Session to use

        Returns:
            New access token

        Raises:
            TokenError: If token request fails
        """
        url = self._get_oauth_url(region)

        try:
            response = session.post(
                url, auth=(self.client_id, self.client_secret), data={"grant_type": "client_credentials"}, timeout=10
            )

            if response.status_code != 200:
                raise TokenError(
                    f"Failed to obtain token: {response.status_code}",
                    status_code=response.status_code,
                    request_url=url,
                    response_data=response.json() if response.text else None,
                )

            data = response.json()
            self._token = data["access_token"]
            self._token_type = data["token_type"]
            self._expires_at = time.time() + data["expires_in"]

            return self._token

        except requests.RequestException as e:
            raise TokenError(f"Token request failed: {str(e)}", request_url=url)

    async def _fetch_token_async(self, region: str, session: aiohttp.ClientSession) -> str:
        """Fetch new access token (asynchronous).

        Args:
            region: API region for OAuth endpoint
            session: aiohttp ClientSession to use

        Returns:
            New access token

        Raises:
            TokenError: If token request fails
        """
        url = self._get_oauth_url(region)

        try:
            async with session.post(
                url,
                auth=aiohttp.BasicAuth(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:

                if response.status != 200:
                    response_data = await response.json() if response.content_type == "application/json" else None
                    raise TokenError(
                        f"Failed to obtain token: {response.status}",
                        status_code=response.status,
                        request_url=url,
                        response_data=response_data,
                    )

                data = await response.json()
                self._token = data["access_token"]
                self._token_type = data["token_type"]
                self._expires_at = time.time() + data["expires_in"]

                return self._token

        except aiohttp.ClientError as e:
            raise TokenError(f"Token request failed: {str(e)}", request_url=url)

    def invalidate(self) -> None:
        """Invalidate current token, forcing a refresh on next request."""
        self._token = None
        self._expires_at = None

    @staticmethod
    def _get_oauth_url(region: str) -> str:
        """Get OAuth URL for region.

        Args:
            region: API region

        Returns:
            OAuth token endpoint URL
        """
        if region == "cn":
            return "https://oauth.battlenet.com.cn/token"
        return f"https://{region}.battle.net/oauth/token"
