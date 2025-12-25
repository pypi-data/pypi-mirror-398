from bosa_core import ConfigService as ConfigService
from bosa_core.authentication.client.service import ClientAwareService as ClientAwareService
from bosa_core.authentication.token.service import VerifyTokenService as VerifyTokenService
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.code_interpreter.routes.execute_code import ExecuteCodeRoutes as ExecuteCodeRoutes
from bosa_server_plugins.common.helper.header import HeaderHelper as HeaderHelper
from bosa_server_plugins.handler.auth.api_key import ApiKeyAuthenticationSchema as ApiKeyAuthenticationSchema
from bosa_server_plugins.handler.header import ExposedDefaultHeaders as ExposedDefaultHeaders
from bosa_server_plugins.handler.router import Router as Router
from typing import Callable

class CodeInterpreterApiRoutes:
    """Code Interpreter API Routes.

    Attributes:
        INTEGRATION_NAME (str): The name of the integration.
        router (Router): The router instance.
        config (ConfigService): The config service instance.
        _get_default_auth_scheme (Callable[[], AuthenticationScheme]): The function to get the default authentication
            scheme.
        _third_party_integration_service (ThirdPartyIntegrationService): The third party integration service instance.
        header_helper (HeaderHelper): The header helper instance.
    """
    INTEGRATION_NAME: str
    router: Router
    config: ConfigService
    header_helper: HeaderHelper
    def __init__(self, router: Router, config: ConfigService, get_default_auth_scheme: Callable[[], AuthenticationScheme], client_aware_service: ClientAwareService, token_service: VerifyTokenService) -> None:
        """Initialize Code Interpreter API Routes.

        Args:
            router (Router): Router instance
            config (ConfigService): Config service
            get_default_auth_scheme (Callable[[], AuthenticationScheme]): Function to get the default authentication
                scheme
            client_aware_service (ClientAwareService): Client aware service
            token_service (VerifyTokenService): Verify token service
            third_party_integration_service (ThirdPartyIntegrationService): Third party integration service
        """
