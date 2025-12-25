from bosa_core import ConfigService as ConfigService
from bosa_core.authentication.client.service import ClientAwareService as ClientAwareService
from bosa_core.authentication.plugin.service import ThirdPartyIntegrationService as ThirdPartyIntegrationService
from bosa_core.authentication.token.service import VerifyTokenService as VerifyTokenService
from bosa_server_plugins.common.auth.custom import CustomAuthenticationScheme as CustomAuthenticationScheme
from bosa_server_plugins.common.auth.responses import PluginAuthenticationSchemeResponse as PluginAuthenticationSchemeResponse
from bosa_server_plugins.common.exception import IntegrationDoesNotExistException as IntegrationDoesNotExistException
from bosa_server_plugins.common.helper.header import HeaderHelper as HeaderHelper
from bosa_server_plugins.common.plugin import ThirdPartyIntegrationPlugin as ThirdPartyIntegrationPlugin
from bosa_server_plugins.github_copilot_analytics.config import GithubCopilotAnalyticsConfig as GithubCopilotAnalyticsConfig
from bosa_server_plugins.github_copilot_analytics.router import GithubCopilotAnalyticsRouter as GithubCopilotAnalyticsRouter
from bosa_server_plugins.handler.header import ExposedDefaultHeaders as ExposedDefaultHeaders
from bosa_server_plugins.handler.router import Router as Router
from typing import Any

class GithubCopilotAnalyticsPlugin(ThirdPartyIntegrationPlugin):
    """GitHub Copilot Analytics Plugin."""
    name: str
    version: str
    description: str
    icon: str
    config: ConfigService
    router: Router
    client_aware_service: ClientAwareService
    token_service: VerifyTokenService
    third_party_integration_service: ThirdPartyIntegrationService
    header_helper: HeaderHelper
    routes: GithubCopilotAnalyticsRouter
    def __init__(self) -> None:
        """Initializes the plugin."""
    def available_auth_schemes(self) -> PluginAuthenticationSchemeResponse:
        """Get the available authentication schemes.

        Returns:
            PluginAuthenticationSchemeResponse: The available authentication schemes
        """
    def initialize_authorization(self, callback_url: str, headers: ExposedDefaultHeaders):
        """Initializes the plugin authorization.

        OAuth2 is not supported. Use initialize_custom_configuration instead.

        Args:
            callback_url: The callback URL.
            headers: The headers.

        Raises:
            NotImplementedError: Always raised since OAuth2 is not supported
        """
    def initialize_custom_configuration(self, configuration: dict[str, Any], headers: ExposedDefaultHeaders):
        """Initializes the plugin with custom configuration.

        Args:
            configuration: The custom configuration dictionary.
            Must contain:
                - github_token (required): GitHub Personal Access Token
                - organization (required): GitHub organization name
            headers: The headers.

        Returns:
            dict: Configuration result with integration ID and identifier

        Raises:
            ValueError: If configuration is invalid
        """
    def success_authorize_callback(self, **kwargs) -> None:
        """Callback for successful authorization.

        Not supported for this plugin.

        Args:
            **kwargs: The keyword arguments.

        Raises:
            NotImplementedError: Always raised since OAuth2 is not supported
        """
    def remove_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Removes the integration.

        Args:
            user_identifier: The user identifier (organization name) to remove.
            headers: The headers.
        """
    def user_has_integration(self, headers: ExposedDefaultHeaders):
        """Checks if the user has an integration.

        Args:
            headers: The headers.

        Returns:
            bool: True if the user has an integration, False otherwise.
        """
    def select_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Selects the integration.

        Args:
            user_identifier: The user identifier (organization name) to select.
            headers: The headers.
        """
    def get_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Get the integration.

        Args:
            user_identifier: The user identifier (organization name).
            headers: The headers.

        Returns:
            The integration object
        """
