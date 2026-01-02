"""World of Warcraft API facade."""

from ..core import BaseClient, EndpointRegistry, MethodFactory, RequestExecutor


class WowGameDataAPI:
    """WoW Game Data API with dynamically generated methods."""

    def __init__(self, client: BaseClient, executor: RequestExecutor, registry: EndpointRegistry):
        """Initialize WoW Game Data API.

        Args:
            client: Base client for session management
            executor: Request executor
            registry: Endpoint registry
        """
        self.client = client
        self.executor = executor
        self.registry = registry

        # Generate and attach all methods
        factory = MethodFactory(executor, registry)
        methods = factory.generate_all_methods("wow", "game_data")

        for method_name, (sync_method, async_method) in methods.items():
            # Bind methods to this instance
            setattr(self, method_name, sync_method.__get__(self, type(self)))
            setattr(self, f"{method_name}_async", async_method.__get__(self, type(self)))


class WowProfileAPI:
    """WoW Profile API with dynamically generated methods."""

    def __init__(self, client: BaseClient, executor: RequestExecutor, registry: EndpointRegistry):
        """Initialize WoW Profile API.

        Args:
            client: Base client for session management
            executor: Request executor
            registry: Endpoint registry
        """
        self.client = client
        self.executor = executor
        self.registry = registry

        # Generate and attach all methods
        factory = MethodFactory(executor, registry)
        methods = factory.generate_all_methods("wow", "profile")

        for method_name, (sync_method, async_method) in methods.items():
            # Bind methods to this instance
            setattr(self, method_name, sync_method.__get__(self, type(self)))
            setattr(self, f"{method_name}_async", async_method.__get__(self, type(self)))


class WowAPI:
    """World of Warcraft API facade.

    Provides access to:
    - game_data: WoW Game Data API (achievements, items, etc.)
    - profile: WoW Profile API (characters, guilds, etc.)
    """

    def __init__(self, client: BaseClient, registry: EndpointRegistry):
        """Initialize WoW API.

        Args:
            client: Base client for session management
            registry: Endpoint registry
        """
        self.client = client
        executor = RequestExecutor(client.token_manager)

        # Initialize sub-APIs
        self.game_data = WowGameDataAPI(client, executor, registry)
        self.profile = WowProfileAPI(client, executor, registry)
