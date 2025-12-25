from _typeshed import Incomplete
from bosa_core import ConfigService as ConfigService
from bosa_core.authentication.client.service import ClientAwareService as ClientAwareService
from bosa_core.authentication.plugin.repository.models import ThirdPartyIntegrationAuth as ThirdPartyIntegrationAuth
from bosa_core.authentication.plugin.service import ThirdPartyIntegrationService as ThirdPartyIntegrationService
from bosa_core.authentication.token.service.verify_token_service import VerifyTokenService as VerifyTokenService
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.common.helper.header import HeaderHelper as HeaderHelper
from bosa_server_plugins.common.helper.integration import IntegrationDoesNotExistException as IntegrationDoesNotExistException
from bosa_server_plugins.handler import ExposedDefaultHeaders as ExposedDefaultHeaders, Router as Router
from bosa_server_plugins.twitter.auth.auth import TwitterClient as TwitterClient
from bosa_server_plugins.twitter.routes.tweets import TweetRoutes as TweetRoutes
from bosa_server_plugins.twitter.routes.users import UserRoutes as UserRoutes
from typing import Callable

class TwitterApiRoutes:
    """Defines and registers Twitter-related API routes with a FastAPI router.

    This class is responsible for initializing and organizing all Twitter endpoint
    routes, such as tweet search or thread retrieval, using the provided Twitter API token.
    """
    INTEGRATION_NAME: str
    router: Router
    config: ConfigService
    header_helper: HeaderHelper
    TWITTER_TOKEN_URL: str
    DEFAULT_TIMEOUT: int
    client_aware_service: Incomplete
    verify_token_service: Incomplete
    def __init__(self, router: Router, get_default_auth_scheme: Callable[[], AuthenticationScheme], client_aware_service: ClientAwareService, verify_token_service: VerifyTokenService, config: ConfigService, third_party_integration_service: ThirdPartyIntegrationService) -> None:
        """Initialize Twitter API Routes.

        Args:
            router: Router instance
            get_default_auth_scheme: Function to get the default authentication scheme
            client_aware_service: Client aware service
            verify_token_service: Verify token service
            third_party_integration_service: ThirdPartyIntegrationService
            config: Config service
        """
