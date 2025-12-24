"""Main BlizzardAPI client."""

from .api import WowAPI
from .core import BaseClient, EndpointRegistry
from .types import Locale, Region


class BlizzardAPI(BaseClient):
    """Main Blizzard API client.

    Provides access to all Blizzard game APIs with proper session management,
    authentication, and error handling.

    Example:
        Synchronous usage:
            with BlizzardAPI(client_id, client_secret) as api:
                data = api.wow.game_data.get_achievement(
                    region="us",
                    locale="en_US",
                    achievement_id=6
                )

        Asynchronous usage:
            async with BlizzardAPI(client_id, client_secret) as api:
                data = await api.wow.game_data.get_achievement_async(
                    region="us",
                    locale="en_US",
                    achievement_id=6
                )
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        region: Region | str = Region.US,
        locale: Locale | str | None = None,
    ):
        """Initialize Blizzard API client.

        Args:
            client_id: Blizzard API client ID
            client_secret: Blizzard API client secret
            region: Default region (defaults to US)
            locale: Default locale (defaults to region's default)
        """
        super().__init__(client_id, client_secret, region, locale)

        # Initialize endpoint registry
        self.registry = EndpointRegistry()

        # Initialize game APIs
        self.wow = WowAPI(self, self.registry)
