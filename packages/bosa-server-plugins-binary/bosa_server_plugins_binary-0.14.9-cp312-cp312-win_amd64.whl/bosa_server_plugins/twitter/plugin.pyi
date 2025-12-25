from .router import TwitterApiRoutes as TwitterApiRoutes
from _typeshed import Incomplete
from bosa_core import ConfigService as ConfigService
from bosa_core.authentication.client.service import ClientAwareService as ClientAwareService
from bosa_core.authentication.plugin.service import ThirdPartyIntegrationService as ThirdPartyIntegrationService
from bosa_core.authentication.token.service.verify_token_service import VerifyTokenService as VerifyTokenService
from bosa_core.cache.interface import CacheService as CacheService
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.common.exception import IntegrationDoesNotExistException as IntegrationDoesNotExistException
from bosa_server_plugins.common.helper.header import HeaderHelper as HeaderHelper
from bosa_server_plugins.common.helper.integration import IntegrationHelper as IntegrationHelper
from bosa_server_plugins.common.plugin import ThirdPartyIntegrationPlugin as ThirdPartyIntegrationPlugin
from bosa_server_plugins.handler.header import ExposedDefaultHeaders as ExposedDefaultHeaders
from bosa_server_plugins.twitter.auth.auth import TwitterClient as TwitterClient
from typing import Any

class TwitterApiPlugin(ThirdPartyIntegrationPlugin):
    """Twitter API Plugin."""
    name: str
    version: str
    description: str
    icon: str
    routes: TwitterApiRoutes
    config: ConfigService
    cache: CacheService
    client_aware_service: ClientAwareService
    verify_token_service: VerifyTokenService
    third_party_integration_service: ThirdPartyIntegrationService
    header_helper: HeaderHelper
    auth_scheme: AuthenticationScheme
    auth_scopes: Incomplete
    TWITTER_AUTH_URL: str
    TWITTER_TOKEN_URL: str
    TWITTER_REVOKE_TOKEN_URL: str
    DEFAULT_CODE_VERIFIER_LENGTH: int
    DEFAULT_TIMEOUT: int
    integration_helper: Incomplete
    def __init__(self) -> None:
        """Initializes Twitter API plugin."""
    def initialize_authorization(self, callback_url: str, headers: ExposedDefaultHeaders):
        """Initializes the plugin authorization.

        Args:
            callback_url: The callback URL.
            headers: The headers.

        Returns:
            The authorization URL.

        Notes:
            This implementation does not support multiple users yet.
            Currently, the request is using the master key.
        """
    def initialize_custom_configuration(self, configuration: dict[str, Any], headers: ExposedDefaultHeaders):
        """Initializes the plugin with custom configuration.

        Args:
            configuration: The custom configuration dictionary.
            headers: The headers.

        Raises:
            NotImplementedError: If the custom configuration is not supported by this plugin.
        """
    def success_authorize_callback(self, **kwargs):
        """Callback for successful authorization.

        Args:
            **kwargs: The keyword arguments.
        """
    def remove_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Removes the integration.

        Args:
            user_identifier: The user identifier to remove.
            headers: The headers.
        """
    def user_has_integration(self, headers: ExposedDefaultHeaders):
        """Checks if the user has an integration.

        Args:
            headers: The headers.

        Returns:
            True if the user has an integration, False otherwise.
        """
    def select_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Selects the integration.

        Args:
            user_identifier: The user identifier.
            headers: The headers.
        """
    def get_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Get the integration.

        Args:
            user_identifier: The user identifier.
            headers: The headers.
        """
