"""Base API client with session management."""

import aiohttp
import requests

from ..types import Locale, Region, get_default_locale
from .auth import TokenManager


class BaseClient:
    """Base API client with proper session management.

    Manages HTTP sessions for both sync and async requests,
    with automatic cleanup via context managers.

    Example:
        Synchronous usage:
            with BaseClient(client_id, client_secret) as client:
                # Use client
                pass

        Asynchronous usage:
            async with BaseClient(client_id, client_secret) as client:
                # Use client
                pass
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        region: Region | str = Region.US,
        locale: Locale | str | None = None,
    ):
        """Initialize API client.

        Args:
            client_id: Blizzard API client ID
            client_secret: Blizzard API client secret
            region: Default region (defaults to US)
            locale: Default locale (defaults to region's default locale)
        """
        self.client_id = client_id
        self.client_secret = client_secret

        # Convert region to enum if string
        if isinstance(region, str):
            self.default_region = Region(region)
        else:
            self.default_region = region

        # Set default locale
        if locale is None:
            self.default_locale = get_default_locale(self.default_region)
        elif isinstance(locale, str):
            self.default_locale = Locale(locale)
        else:
            self.default_locale = locale

        # Session management
        self._sync_session: requests.Session | None = None
        self._async_session: aiohttp.ClientSession | None = None

        # Token manager (shared between sync and async)
        self.token_manager = TokenManager(client_id, client_secret)

    @property
    def sync_session(self) -> requests.Session:
        """Get or create synchronous session.

        Returns:
            Active requests.Session instance
        """
        if self._sync_session is None:
            self._sync_session = requests.Session()
        return self._sync_session

    @property
    def async_session(self) -> aiohttp.ClientSession:
        """Get or create asynchronous session.

        Returns:
            Active aiohttp.ClientSession instance
        """
        if self._async_session is None or self._async_session.closed:
            self._async_session = aiohttp.ClientSession()
        return self._async_session

    def close(self) -> None:
        """Close synchronous session."""
        if self._sync_session is not None:
            self._sync_session.close()
            self._sync_session = None

    async def aclose(self) -> None:
        """Close asynchronous session."""
        if self._async_session is not None and not self._async_session.closed:
            await self._async_session.close()
            self._async_session = None

    # Context manager support (sync)

    def __enter__(self):
        """Enter synchronous context manager.

        Returns:
            Self for context manager usage
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit synchronous context manager.

        Closes sync session automatically.
        """
        self.close()

    # Async context manager support

    async def __aenter__(self):
        """Enter asynchronous context manager.

        Returns:
            Self for async context manager usage
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit asynchronous context manager.

        Closes async session automatically.
        """
        await self.aclose()

    def __del__(self):
        """Cleanup on deletion.

        Attempts to close sessions if they're still open.
        """
        try:
            if self._sync_session is not None:
                self._sync_session.close()
        except Exception:
            pass
