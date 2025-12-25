from _typeshed import Incomplete
from bosa_core.authentication.token.service import VerifyTokenService as VerifyTokenService
from bosa_server_plugins.handler.auth.schema import AuthenticationSchema as AuthenticationSchema
from bosa_server_plugins.handler.header import HttpHeaders as HttpHeaders
from bosa_server_plugins.handler.mcp.header_manager import BOSA_HEADERS_STATE_KEY as BOSA_HEADERS_STATE_KEY, has_api_key as has_api_key, process_colon_separated_api_key as process_colon_separated_api_key
from fastmcp.server.auth import AccessToken, TokenVerifier
from starlette.requests import Request as Request

logger: Incomplete

class BosaTokenVerifier(TokenVerifier):
    """Verify BOSA-issued tokens before falling back to Google OAuth tokens."""
    STATE_HEADER_KEY = BOSA_HEADERS_STATE_KEY
    def __init__(self, *, required_scopes: list[str] | None = None, google_timeout_seconds: int = 10, authentication_schema: AuthenticationSchema | None = None, verify_token_service: VerifyTokenService | None = None) -> None: ...
    async def verify_token(self, token: str) -> AccessToken | None:
        """Try to validate BOSA tokens first, then fall back to Google.

        Args:
            token: The token to validate.

        Returns:
            AccessToken | None: The validated token.
        """
    def set_authentication_schema(self, authentication_schema: AuthenticationSchema | None) -> None:
        """Attach an authentication schema for API-key validation.

        Args:
            authentication_schema: The authentication schema to attach.
        """
    def set_verify_token_service(self, verify_token_service: VerifyTokenService | None) -> None:
        """Attach a token verification service for user lookup.

        Args:
            verify_token_service: The token verification service to attach.
        """
    async def verify_bosa_only(self, token: str) -> AccessToken | None:
        """Verify only against BOSA headers without falling back to Google.

        Args:
            token: The token to validate.

        Returns:
            AccessToken | None: The validated token.
        """
