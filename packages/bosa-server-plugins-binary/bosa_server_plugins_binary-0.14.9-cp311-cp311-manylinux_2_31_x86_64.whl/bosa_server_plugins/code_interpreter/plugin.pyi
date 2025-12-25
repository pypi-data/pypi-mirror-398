from _typeshed import Incomplete
from bosa_core import ConfigService as ConfigService
from bosa_core.authentication.client.service import ClientAwareService as ClientAwareService
from bosa_core.authentication.plugin.service import ThirdPartyIntegrationService as ThirdPartyIntegrationService
from bosa_core.authentication.token.service import VerifyTokenService as VerifyTokenService
from bosa_core.cache import CacheService as CacheService
from bosa_server_plugins.auth.bearer import BearerTokenAuthentication as BearerTokenAuthentication
from bosa_server_plugins.code_interpreter.constant import E2B_API_KEY_ENV as E2B_API_KEY_ENV, E2B_DOMAIN_ENV as E2B_DOMAIN_ENV, E2B_TEMPLATE_PYTHON_ENV as E2B_TEMPLATE_PYTHON_ENV
from bosa_server_plugins.code_interpreter.router import CodeInterpreterApiRoutes as CodeInterpreterApiRoutes
from bosa_server_plugins.common.auth.responses import PluginAuthenticationSchemeResponse as PluginAuthenticationSchemeResponse
from bosa_server_plugins.common.helper.header import HeaderHelper as HeaderHelper
from bosa_server_plugins.common.plugin import ThirdPartyIntegrationPlugin as ThirdPartyIntegrationPlugin
from bosa_server_plugins.handler import ExposedDefaultHeaders as ExposedDefaultHeaders, Router as Router
from typing import Any

class CodeInterpreterPlugin(ThirdPartyIntegrationPlugin):
    """Code Interpreter Plugin."""
    name: str
    version: str
    description: str
    config: ConfigService
    cache: CacheService
    router: Router
    client_aware_service: ClientAwareService
    third_party_integration_service: ThirdPartyIntegrationService
    token_service: VerifyTokenService
    header_helper: HeaderHelper
    api_key: Incomplete
    domain: Incomplete
    template_id: Incomplete
    auth_scheme: BearerTokenAuthentication | None
    routes: Incomplete
    def __init__(self) -> None:
        """Initializes the plugin."""
    def available_auth_schemes(self) -> PluginAuthenticationSchemeResponse:
        """Returns the available authentication schemes.

        Returns:
            PluginAuthenticationSchemeResponse: The available authentication schemes
        """
    def initialize_authorization(self, callback_url: str, headers: ExposedDefaultHeaders):
        """Initializes the plugin authorization.

        This method is not supported by this plugin. Use initialize_custom_configuration instead.

        Args:
            callback_url (str): The callback URL.
            headers (ExposedDefaultHeaders): The headers.

        Raises:
            RuntimeError: If the plugin is disabled due to missing configuration.
            NotImplementedError: because this plugin does not support OAuth2 authorization.
        """
    def initialize_custom_configuration(self, configuration: dict[str, Any], headers: ExposedDefaultHeaders):
        """Initializes the plugin with custom configuration.

        Args:
            configuration (dict[str, Any]): The custom configuration dictionary containing the API key.
            headers (ExposedDefaultHeaders): The headers.

        Returns:
            dict: Dictionary containing configuration_id and configuration_name.

        Raises:
            RuntimeError: If the plugin is disabled due to missing configuration.
            NotImplementedError: because this plugin does not support custom configuration.
        """
    def success_authorize_callback(self, **kwargs) -> None:
        """Success authorize callback.

        This method is not supported by this plugin. Use success_custom_configuration instead.

        Args:
            **kwargs: The keyword arguments.

        Raises:
            RuntimeError: If the plugin is disabled due to missing configuration.
            NotImplementedError: because this plugin does not support OAuth2 authorization.
        """
    def remove_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Removes the integration.

        Args:
            user_identifier (str): The user identifier to remove.
            headers (ExposedDefaultHeaders): The headers.

        Raises:
            RuntimeError: If the plugin is disabled due to missing configuration.
            NotImplementedError: because this plugin does not support removing integration.
        """
    def user_has_integration(self, headers: ExposedDefaultHeaders):
        """Checks if the user has an integration.

        Args:
            headers (ExposedDefaultHeaders): The headers.

        Returns:
            bool: True if the user has an integration, False otherwise.
        """
    def select_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Selects the integration.

        Args:
            user_identifier (str): The user identifier to select.
            headers (ExposedDefaultHeaders): The headers.

        Raises:
            RuntimeError: If the plugin is disabled due to missing configuration.
            NotImplementedError: because this plugin does not support selecting integration.
        """
    def get_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Gets the integration.

        Args:
            user_identifier (str): The user identifier to get.
            headers (ExposedDefaultHeaders): The headers.

        Raises:
            RuntimeError: If the plugin is disabled due to missing configuration.
            NotImplementedError: because this plugin does not support getting integration.
        """
