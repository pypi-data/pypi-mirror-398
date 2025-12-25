from bosa_core.authentication.client.repository.models import ClientModel as ClientModel
from bosa_core.authentication.client.service import ClientAwareService as ClientAwareService
from bosa_core.authentication.token.service import VerifyTokenService as VerifyTokenService
from bosa_server_plugins.handler.header import ExposedDefaultHeaders as ExposedDefaultHeaders
from uuid import UUID

class HeaderHelper:
    """Helper class for header operations."""
    BEARER_TOKEN_PREFIX: str
    client_aware_service: ClientAwareService
    token_service: VerifyTokenService
    def __init__(self, client_aware_service: ClientAwareService, token_service: VerifyTokenService) -> None:
        """Initialize the header helper with required services.

        Args:
            client_aware_service: The client aware service.
            token_service: The token service.
        """
    def get_client_and_user_id_from_http_headers(self, headers: ExposedDefaultHeaders) -> tuple[ClientModel, UUID]:
        """Gather the client and user id from the headers.

        Args:
            headers: The headers.

        Returns:
            The client and user id.
        """
