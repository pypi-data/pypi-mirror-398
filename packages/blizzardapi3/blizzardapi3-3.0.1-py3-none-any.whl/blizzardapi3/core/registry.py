"""Endpoint registry for loading YAML configurations."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class PatternTemplate(BaseModel):
    """Reusable endpoint pattern template.

    Attributes:
        path_template: URL path template with {placeholders}
        params: List of parameter names
        namespace_type: Type of namespace (static, dynamic, profile, none)
        supports_classic: Whether this supports Classic WoW
        accepts_kwargs: Whether this accepts **kwargs for search params
        auth_type: Authentication type (client_credentials or oauth)
    """

    path_template: str
    params: list[str]
    namespace_type: str = "static"
    supports_classic: bool = False
    accepts_kwargs: bool = False
    auth_type: str = "client_credentials"


class EndpointDefinition(BaseModel):
    """Definition of a single API endpoint.

    Attributes:
        method_name: Name of the generated method
        pattern: Pattern template to use
        resource: Resource name for path substitution
        path: Custom path (overrides pattern template)
        params: Custom params (overrides pattern params)
        param_name: Specific parameter name (e.g., achievement_id)
        namespace_type: Override namespace type
        namespace_variant: Special namespace (e.g., dynamic-classic)
        supports_classic: Whether this supports Classic WoW
        description: Method description for docstring
        response_model: Pydantic model name for response
    """

    method_name: str
    pattern: str | None = None
    resource: str = ""
    path: str | None = None
    path_template: str | None = None
    params: list[str] | None = None
    param_name: str | None = None
    namespace_type: str | None = None
    namespace_variant: str | None = None
    supports_classic: bool = False
    accepts_kwargs: bool = False
    http_method: str = "GET"
    description: str
    response_model: str | None = None


class EndpointConfig(BaseModel):
    """Complete endpoint configuration file.

    Attributes:
        version: Config version
        game: Game name (wow, diablo3, hearthstone, starcraft2)
        api_type: API type (game_data, profile, community)
        pattern_templates: Reusable pattern definitions
        endpoints: List of endpoint definitions
    """

    version: str
    game: str
    api_type: str
    pattern_templates: dict[str, PatternTemplate] | None = None
    endpoints: list[EndpointDefinition]


class EndpointRegistry:
    """Registry of all API endpoints loaded from YAML configs.

    Loads and manages endpoint configurations from YAML files,
    providing access to endpoint definitions for method generation.
    """

    def __init__(self, config_dir: Path | str | None = None):
        """Initialize endpoint registry.

        Args:
            config_dir: Directory containing YAML config files
                       (defaults to package config/endpoints)
        """
        if config_dir is None:
            # Default to package config directory
            package_dir = Path(__file__).parent.parent
            self.config_dir = package_dir / "config" / "endpoints"
        else:
            self.config_dir = Path(config_dir)

        self.configs: dict[str, EndpointConfig] = {}
        self._load_all_configs()

    def _load_all_configs(self) -> None:
        """Load all YAML configuration files from config directory."""
        if not self.config_dir.exists():
            # Config directory doesn't exist yet (during development)
            return

        for yaml_file in self.config_dir.glob("*.yaml"):
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    config = EndpointConfig(**data)
                    key = f"{config.game}_{config.api_type}"
                    self.configs[key] = config
            except Exception as e:
                # Log warning but don't fail - allows partial configs during development
                print(f"Warning: Failed to load config {yaml_file}: {e}")

    def get_config(self, game: str, api_type: str) -> EndpointConfig:
        """Get configuration for a specific game/API type.

        Args:
            game: Game name (e.g., "wow", "diablo3")
            api_type: API type (e.g., "game_data", "profile")

        Returns:
            Endpoint configuration

        Raises:
            KeyError: If configuration not found
        """
        key = f"{game}_{api_type}"
        if key not in self.configs:
            raise KeyError(f"No configuration found for {game}/{api_type}")
        return self.configs[key]

    def get_endpoints(self, game: str, api_type: str) -> list[EndpointDefinition]:
        """Get all endpoints for a game/API type.

        Args:
            game: Game name
            api_type: API type

        Returns:
            List of endpoint definitions
        """
        config = self.get_config(game, api_type)
        return config.endpoints

    def resolve_pattern(self, game: str, api_type: str, endpoint: EndpointDefinition) -> PatternTemplate:
        """Resolve pattern template for an endpoint.

        Args:
            game: Game name
            api_type: API type
            endpoint: Endpoint definition

        Returns:
            Resolved pattern template

        Raises:
            KeyError: If pattern template not found
        """
        # If endpoint has custom path_template, create an inline pattern
        if endpoint.path_template is not None:
            return PatternTemplate(
                path_template=endpoint.path_template,
                params=endpoint.params or [],
                namespace_type=endpoint.namespace_type or "none",
                supports_classic=endpoint.supports_classic,
                accepts_kwargs=endpoint.accepts_kwargs,
            )

        # Otherwise, resolve from pattern_templates
        config = self.get_config(game, api_type)
        if endpoint.pattern is None:
            raise KeyError("Endpoint must have either 'pattern' or 'path_template'")
        if config.pattern_templates is None or endpoint.pattern not in config.pattern_templates:
            raise KeyError(f"Pattern template '{endpoint.pattern}' not found")
        return config.pattern_templates[endpoint.pattern]

    def register_custom_config(self, key: str, config_data: dict[str, Any]) -> None:
        """Register a custom endpoint configuration.

        Allows users to add custom endpoints without modifying package files.

        Args:
            key: Configuration key (e.g., "wow_custom")
            config_data: Configuration dictionary matching EndpointConfig schema
        """
        config = EndpointConfig(**config_data)
        self.configs[key] = config

    def list_available_configs(self) -> list[str]:
        """List all available configuration keys.

        Returns:
            List of configuration keys (e.g., ["wow_game_data", "wow_profile"])
        """
        return list(self.configs.keys())
