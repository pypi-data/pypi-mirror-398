from bosa_core.authentication.client.service import ClientAwareService as ClientAwareService
from bosa_core.authentication.plugin.service import ThirdPartyIntegrationService as ThirdPartyIntegrationService
from bosa_core.authentication.token.service import VerifyTokenService as VerifyTokenService
from bosa_server_plugins.common.exception import IntegrationDoesNotExistException as IntegrationDoesNotExistException
from bosa_server_plugins.common.helper.header import HeaderHelper as HeaderHelper
from bosa_server_plugins.cursor_analytics.auth.basic_auth import BasicAuthAuthentication as BasicAuthAuthentication
from bosa_server_plugins.cursor_analytics.routes.analytics import CursorAnalyticsRoutes as CursorAnalyticsRoutes
from bosa_server_plugins.handler.auth.api_key import ApiKeyAuthenticationSchema as ApiKeyAuthenticationSchema
from bosa_server_plugins.handler.header import ExposedDefaultHeaders as ExposedDefaultHeaders
from bosa_server_plugins.handler.router import Router as Router

class CursorAnalyticsRouter:
    """Router for Cursor Analytics API."""
    INTEGRATION_NAME: str
    DEFAULT_API_URL: str
    router: Router
    header_helper: HeaderHelper
    third_party_integration_service: ThirdPartyIntegrationService
    def __init__(self, router: Router, client_aware_service: ClientAwareService, token_service: VerifyTokenService, third_party_integration_service: ThirdPartyIntegrationService) -> None:
        """Initialize Cursor Analytics router.

        Args:
            router: Router instance
            client_aware_service: Client aware service
            token_service: Verify token service
            third_party_integration_service: Third party integration service
        """
