import abc
from abc import abstractmethod
from bosa_core import Plugin
from bosa_server_plugins.common.auth.oauth2 import OAuth2AuthenticationScheme as OAuth2AuthenticationScheme
from bosa_server_plugins.common.auth.responses import PluginAuthenticationSchemeResponse as PluginAuthenticationSchemeResponse
from bosa_server_plugins.common.exception import BosaOAuth2ErrorEnum as BosaOAuth2ErrorEnum, InvalidOAuth2StateException as InvalidOAuth2StateException, OAuth2CallbackException as OAuth2CallbackException
from bosa_server_plugins.common.helper.integration import IntegrationHelper as IntegrationHelper
from bosa_server_plugins.common.requests import AuthorizationRequest as AuthorizationRequest
from bosa_server_plugins.handler.decorators import public as public
from bosa_server_plugins.handler.header import ExposedDefaultHeaders as ExposedDefaultHeaders
from bosa_server_plugins.handler.interface import HttpHandler as HttpHandler
from bosa_server_plugins.handler.model import BaseRequestModel as BaseRequestModel
from bosa_server_plugins.handler.router import HttpMethod as HttpMethod, Router as Router
from bosa_server_plugins.utils.request import append_query_param as append_query_param
from starlette.requests import Request as Request
from typing import Any

class RemoteServerPlugin(Plugin, metaclass=abc.ABCMeta):
    """Remote Plugin base class.

    This class provides the foundation for creating plugins that communicate with
    remote servers. It handles tool discovery, route generation,
    and request/response translation between HTTP and remote protocols.
    """
    router: Router
    base_url: str
    tools: dict[str, Any]
    icon: str | None
    integration_helper: IntegrationHelper | None
    oauth2_error_mapping: dict[Any, BosaOAuth2ErrorEnum]
    def __init__(self) -> None:
        """Initialize the MCP Remote Server Plugin."""
    @abstractmethod
    def initialize_authorization(self, callback_url: str, headers: ExposedDefaultHeaders):
        """Initializes the plugin authorization.

        Args:
            callback_url: The callback URL.
            headers: The headers.

        Returns:
            The authorization URL.
        """
    @abstractmethod
    def initialize_custom_configuration(self, configuration: dict[str, Any], headers: ExposedDefaultHeaders):
        """Initializes the plugin with custom configuration.

        Args:
            configuration: The custom configuration dictionary.
            headers: The headers.

        Returns:
            The configuration result URL or status.
        """
    @abstractmethod
    def success_authorize_callback(self, **kwargs) -> str:
        """Callback for successful authorization.

        Args:
            **kwargs: The keyword arguments.

        Returns:
            str: The user identifier.
        """
    @abstractmethod
    def remove_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Removes the integration.

        Args:
            user_identifier: The user identifier to remove.
            headers: The headers.
        """
    @abstractmethod
    def user_has_integration(self, headers: ExposedDefaultHeaders):
        """Checks if the user has an integration.

        Args:
            headers: The headers.

        Returns:
            True if the user has an integration, False otherwise.
        """
    @abstractmethod
    def select_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Selects the integration.

        Args:
            user_identifier: The user identifier to select.
            headers: The headers.
        """
    @abstractmethod
    def get_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Get the integration.

        Args:
            user_identifier: The user identifier to select.
            headers: The headers.
        """
    def available_auth_schemes(self) -> PluginAuthenticationSchemeResponse:
        """Get the available authentication schemes.

        Returns:
            PluginAuthenticationSchemeResponse: The available authentication schemes
        """
    async def ensure_tools_loaded(self) -> bool:
        """Ensure tools are loaded from the MCP server.

        This method checks if tools are already loaded and attempts to load them
        if they are not available. It provides a fallback mechanism for tool loading.

        Returns:
            bool: True if tools are available, False otherwise
        """
    @abstractmethod
    async def execute_tool(self, tool_name: str, arguments: dict[str, Any] | None = None, headers: ExposedDefaultHeaders | None = None) -> Any:
        """Execute a specific tool with given arguments.

        This abstract method must be implemented by subclasses to define how tools
        are executed on the specific remote server implementation.

        Args:
            tool_name (str): Name of the tool to execute
            arguments (Optional[Dict[str, Any]]): Arguments to pass to the tool. Defaults to None.
            headers (Optional[ExposedDefaultHeaders]): Headers to pass to the tool. Defaults to None.

        Returns:
            Any: Result of the tool execution
        """
    async def generate_tools(self) -> dict[str, Any] | None:
        """Generate and register tools from the remote server.

        This method orchestrates the tool generation process by:
        1. Fetching tools from the remote server using _fetch_tools()
        2. Updating the internal tools dictionary
        3. Setting up HTTP routes for each tool

        Returns:
            Optional[Dict[str, Any]]: Dictionary containing the loaded tools, or None if generation failed
        """
