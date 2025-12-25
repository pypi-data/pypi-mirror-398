from bosa_server_plugins.handler.mcp.auth.api_key_auth_middleware import ApiKeyToAuthorizationMiddleware as ApiKeyToAuthorizationMiddleware
from bosa_server_plugins.handler.mcp.auth.bosa_token_verifier import BosaTokenVerifier as BosaTokenVerifier
from fastmcp.server.auth import AccessToken as AccessToken
from fastmcp.server.auth.oauth_proxy import OAuthProxy
from mcp.shared.auth import OAuthClientInformationFull as OAuthClientInformationFull
from starlette.middleware import Middleware
from typing import Any
from typing_extensions import override

class BosaOAuthProxy(OAuthProxy):
    """OAuth proxy that prioritizes BOSA-authentication before OAuth verification."""
    def __init__(self, token_verifier: BosaTokenVerifier, allow_extra_client_scopes: bool = True, *args: Any, **kwargs: Any) -> None: ...
    @override
    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        """Accept arbitrary scopes but ensure defaults are populated when missing."""
    async def verify_token(self, token: str) -> AccessToken | None:
        """Accept native BOSA tokens before falling back to standard OAuth tokens."""
    @override
    def get_middleware(self) -> list[Middleware]:
        """Return middleware with X-Api-Key header transformation prepended.

        FastMCP's BearerAuthBackend requires an Authorization header.
        This override injects ApiKeyToAuthorizationMiddleware first to transform
        colon-separated X-Api-Key values into Authorization headers, enabling
        BOSA's legacy authentication format to work with FastMCP.

        Returns:
            list[Middleware]: Middleware stack with header transformation first.
        """
