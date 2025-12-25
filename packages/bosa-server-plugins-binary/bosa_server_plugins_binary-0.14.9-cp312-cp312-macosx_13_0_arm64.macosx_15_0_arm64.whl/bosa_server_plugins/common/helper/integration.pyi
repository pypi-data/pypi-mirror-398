from _typeshed import Incomplete
from bosa_core.authentication.client.service import ClientAwareService as ClientAwareService
from bosa_core.authentication.plugin.repository.models import ThirdPartyIntegrationAuth as ThirdPartyIntegrationAuth
from bosa_core.authentication.plugin.service import ThirdPartyIntegrationService as ThirdPartyIntegrationService
from bosa_core.authentication.token.service import VerifyTokenService as VerifyTokenService
from bosa_core.cache import CacheService as CacheService
from bosa_server_plugins.common.exception import IntegrationDoesNotExistException as IntegrationDoesNotExistException, InvalidOAuth2StateException as InvalidOAuth2StateException
from uuid import UUID

class IntegrationHelper:
    """Helper class for integration operations."""
    DEFAULT_TOKEN_LENGTH: int
    DEFAULT_STATE_TTL: Incomplete
    token_length: int
    state_ttl: int
    connector_name: str
    cache: CacheService
    third_party_integration_service: ThirdPartyIntegrationService
    token_service: VerifyTokenService
    client_aware_service: ClientAwareService
    def __init__(self, connector_name: str, cache: CacheService, third_party_integration_service: ThirdPartyIntegrationService, token_service: VerifyTokenService, client_aware_service: ClientAwareService, token_length: int = ..., state_ttl: int = ...) -> None:
        """Initialize the integration helper with required services.

        Args:
            connector_name: The name of the connector
            cache: The cache service
            third_party_integration_service: The third-party integration service
            token_service: The token service
            client_aware_service: The client-aware service
            token_length: The length of the token
            state_ttl: The TTL of the state
        """
    def create_state_hash(self, args: dict[str, str], callback_url: str) -> str:
        """Creates a state hash that will be validated by our app to ensure security.

        Side-effect: This will also save to cache using cache_service for as long as the
        state_ttl duration.

        Args:
            args: the args to be encoded in the state
            callback_url: the callback url for later use when use has successfully given access.

        Returns:
            State string that comprises the following: args and state_code. State-code is guaranteed to be
            URL-Safe.
        """
    def get_state_data(self, state: str) -> tuple[dict, str]:
        """Get the decoded OAuth2 state data and callback url from the cache.

        Args:
            state: The state to get data from.

        Returns:
            tuple[dict, str]: The decoded state data and callback url.

        Raises:
            InvalidOAuth2StateException: If the state is invalid.
        """
    def get_integration_by_name(self, user_identifier: str, client_id: UUID, user_id: UUID) -> ThirdPartyIntegrationAuth:
        """Get integration by name for a specific connector.

        Args:
            user_identifier: The user identifier to get integration for
            client_id: The client id to get integration for
            user_id: The user id to get integration for

        Returns:
            The integration object.

        Raises:
            IntegrationDoesNotExistException: If integration is not found
        """
