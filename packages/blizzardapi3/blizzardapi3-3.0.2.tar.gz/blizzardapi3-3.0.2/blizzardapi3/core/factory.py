"""Dynamic method factory for generating API methods from configs."""

from collections.abc import Callable
from typing import Any

from .context import RequestContext
from .executor import RequestExecutor
from .registry import EndpointDefinition, EndpointRegistry, PatternTemplate


class MethodFactory:
    """Factory for dynamically generating API methods from endpoint definitions.

    Generates both synchronous and asynchronous method pairs from YAML configs,
    handling parameter construction, URL building, and docstring generation.
    """

    def __init__(self, executor: RequestExecutor, registry: EndpointRegistry):
        """Initialize method factory.

        Args:
            executor: Request executor for making API calls
            registry: Endpoint registry with configuration data
        """
        self.executor = executor
        self.registry = registry

    def create_method_pair(self, game: str, api_type: str, endpoint: EndpointDefinition) -> tuple[Callable, Callable]:
        """Create sync and async method pair from endpoint definition.

        Args:
            game: Game name
            api_type: API type
            endpoint: Endpoint definition

        Returns:
            Tuple of (sync_method, async_method)
        """
        pattern = self.registry.resolve_pattern(game, api_type, endpoint)
        params = self._build_params(endpoint, pattern)

        sync_method = self._create_sync_method(endpoint, pattern, params)
        async_method = self._create_async_method(endpoint, pattern, params)

        return sync_method, async_method

    def _build_params(self, endpoint: EndpointDefinition, pattern: PatternTemplate) -> list[str]:
        """Build parameter list for method signature.

        Args:
            endpoint: Endpoint definition
            pattern: Pattern template

        Returns:
            List of parameter names
        """
        if endpoint.params:
            return endpoint.params

        params = pattern.params.copy()

        # Replace generic 'id' with specific param name
        if endpoint.param_name and "id" in params:
            idx = params.index("id")
            params[idx] = endpoint.param_name

        return params

    def _build_path(self, endpoint: EndpointDefinition, pattern: PatternTemplate, kwargs: dict[str, Any]) -> str:
        """Build request path from template and parameters.

        Args:
            endpoint: Endpoint definition
            pattern: Pattern template
            kwargs: Method arguments

        Returns:
            Formatted path string
        """
        if endpoint.path:
            path_template = endpoint.path
        else:
            path_template = pattern.path_template

        # Build format kwargs
        format_kwargs = {"resource": endpoint.resource}

        # Add any path parameters (anything not region/locale/is_classic/access_token)
        special_params = {"region", "locale", "is_classic", "access_token"}
        for key, value in kwargs.items():
            if key not in special_params:
                # Convert character_name and realm_slug to lowercase for API compatibility
                if key in ("character_name", "realm_slug", "name_slug") and isinstance(value, str):
                    value = value.lower()
                format_kwargs[key] = value

        # Handle generic 'id' parameter
        if "id" in path_template and endpoint.param_name:
            format_kwargs["id"] = kwargs.get(endpoint.param_name)

        return path_template.format(**format_kwargs)

    def _build_namespace(
        self, endpoint: EndpointDefinition, pattern: PatternTemplate, region: str, is_classic: bool = False
    ) -> str | None:
        """Build namespace string.

        Args:
            endpoint: Endpoint definition
            pattern: Pattern template
            region: API region
            is_classic: Whether this is a Classic request

        Returns:
            Namespace string or None
        """
        namespace_type = endpoint.namespace_type or pattern.namespace_type

        if namespace_type == "none":
            return None

        if endpoint.namespace_variant:
            return f"{endpoint.namespace_variant}-{region}"

        supports_classic = endpoint.supports_classic or pattern.supports_classic
        if is_classic and supports_classic:
            return f"{namespace_type}-classic-{region}"

        return f"{namespace_type}-{region}"

    def _create_sync_method(
        self, endpoint: EndpointDefinition, pattern: PatternTemplate, params: list[str]
    ) -> Callable:
        """Create synchronous method.

        Args:
            endpoint: Endpoint definition
            pattern: Pattern template
            params: Parameter list

        Returns:
            Synchronous method callable
        """
        # Capture factory methods in closure
        build_path = self._build_path
        build_namespace = self._build_namespace

        def method(api_instance, **kwargs: Any) -> dict[str, Any]:
            # Validate required params
            for param in params:
                if param not in kwargs:
                    from ..exceptions import MissingParameterError

                    raise MissingParameterError(
                        f"Missing required parameter: {param}", field=param, required_params=params
                    )

            # Extract special params
            region = kwargs.pop("region")
            locale = kwargs.pop("locale")
            is_classic = kwargs.pop("is_classic", False)
            access_token = kwargs.pop("access_token", None)

            # Convert enums to strings
            if hasattr(region, "value"):
                region = region.value
            if hasattr(locale, "value"):
                locale = locale.value

            # Build path using factory method
            path = build_path(endpoint, pattern, kwargs)

            # Build namespace using factory method
            namespace = build_namespace(endpoint, pattern, region, is_classic)

            # Build query params
            query_params = {"locale": locale}
            if namespace:
                query_params["namespace"] = namespace

            # Add remaining kwargs for search/filter params
            if pattern.accepts_kwargs:
                query_params.update(kwargs)

            # Create request context
            context = RequestContext(
                region=region,
                path=path,
                query_params=query_params,
                access_token=access_token,
                auth_type=pattern.auth_type,
            )

            # Execute request
            return api_instance.executor.execute(context, api_instance.client.sync_session)

        # Set method metadata
        method.__name__ = endpoint.method_name
        method.__doc__ = self._generate_docstring(endpoint, params, is_async=False)

        return method

    def _create_async_method(
        self, endpoint: EndpointDefinition, pattern: PatternTemplate, params: list[str]
    ) -> Callable:
        """Create asynchronous method.

        Args:
            endpoint: Endpoint definition
            pattern: Pattern template
            params: Parameter list

        Returns:
            Asynchronous method callable
        """
        # Capture factory methods in closure
        build_path = self._build_path
        build_namespace = self._build_namespace

        async def method(api_instance, **kwargs: Any) -> dict[str, Any]:
            # Validate required params
            for param in params:
                if param not in kwargs:
                    from ..exceptions import MissingParameterError

                    raise MissingParameterError(
                        f"Missing required parameter: {param}", field=param, required_params=params
                    )

            # Extract special params
            region = kwargs.pop("region")
            locale = kwargs.pop("locale")
            is_classic = kwargs.pop("is_classic", False)
            access_token = kwargs.pop("access_token", None)

            # Convert enums to strings
            if hasattr(region, "value"):
                region = region.value
            if hasattr(locale, "value"):
                locale = locale.value

            # Build path using factory method
            path = build_path(endpoint, pattern, kwargs)

            # Build namespace using factory method
            namespace = build_namespace(endpoint, pattern, region, is_classic)

            # Build query params
            query_params = {"locale": locale}
            if namespace:
                query_params["namespace"] = namespace

            # Add remaining kwargs for search/filter params
            if pattern.accepts_kwargs:
                query_params.update(kwargs)

            # Create request context
            context = RequestContext(
                region=region,
                path=path,
                query_params=query_params,
                access_token=access_token,
                auth_type=pattern.auth_type,
            )

            # Execute request
            return await api_instance.executor.execute_async(context, api_instance.client.async_session)

        # Set method metadata
        method.__name__ = f"{endpoint.method_name}_async"
        method.__doc__ = self._generate_docstring(endpoint, params, is_async=True)

        return method

    def _generate_docstring(self, endpoint: EndpointDefinition, params: list[str], is_async: bool = False) -> str:
        """Generate method docstring.

        Args:
            endpoint: Endpoint definition
            params: Parameter list
            is_async: Whether this is an async method

        Returns:
            Formatted docstring
        """
        async_prefix = "Asynchronously " if is_async else ""

        doc = f"""{async_prefix}{endpoint.description}.

Args:
"""

        for param in params:
            param_type = self._get_param_type(param)
            param_desc = self._get_param_description(param)
            doc += f"    {param}: {param_type} - {param_desc}\n"

        # Add optional parameters
        doc += "    is_classic: bool - Whether to use Classic namespace (default: False)\n"
        doc += "    **kwargs: Additional query parameters for search/filter\n"

        if endpoint.response_model:
            doc += f"""
Returns:
    dict[str, Any]: {endpoint.response_model} data

Raises:
    NotFoundError: If the resource is not found
    RateLimitError: If rate limit is exceeded
    BlizzardAPIError: For other API errors
"""
        else:
            doc += """
Returns:
    dict[str, Any]: API response data

Raises:
    NotFoundError: If the resource is not found
    RateLimitError: If rate limit is exceeded
    BlizzardAPIError: For other API errors
"""

        return doc

    def _get_param_type(self, param: str) -> str:
        """Get type hint for parameter.

        Args:
            param: Parameter name

        Returns:
            Type hint string
        """
        if param == "region":
            return "str | Region"
        if param == "locale":
            return "str | Locale"
        if param == "access_token":
            return "str"
        if "_id" in param or param.endswith("_id"):
            return "int"
        return "str"

    def _get_param_description(self, param: str) -> str:
        """Get description for parameter.

        Args:
            param: Parameter name

        Returns:
            Parameter description
        """
        descriptions = {
            "region": 'The region to query (e.g., "us", "eu")',
            "locale": 'The locale for the response (e.g., "en_US")',
            "access_token": "OAuth access token for user-specific endpoints",
        }
        return descriptions.get(param, f'The {param.replace("_", " ")}')

    def generate_all_methods(self, game: str, api_type: str) -> dict[str, tuple[Callable, Callable]]:
        """Generate all methods for a game/API type.

        Args:
            game: Game name
            api_type: API type

        Returns:
            Dictionary mapping method names to (sync_method, async_method) tuples
        """
        endpoints = self.registry.get_endpoints(game, api_type)
        methods = {}

        for endpoint in endpoints:
            sync_method, async_method = self.create_method_pair(game, api_type, endpoint)
            methods[endpoint.method_name] = (sync_method, async_method)

        return methods
