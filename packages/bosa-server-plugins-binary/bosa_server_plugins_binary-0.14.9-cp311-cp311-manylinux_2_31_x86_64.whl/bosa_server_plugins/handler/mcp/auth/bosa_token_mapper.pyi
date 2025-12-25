from _typeshed import Incomplete
from bosa_core.authentication.token.repository.models import TokenComplete as TokenComplete
from bosa_core.authentication.user.repository.models import UserModel as UserModel
from bosa_core.cache.interface import CacheService as CacheService
from fastmcp.server.auth import AccessToken as AccessToken
from typing import Any

class BosaTokenMapper:
    """Map upstream OAuth claims into BOSA-issued tokens."""
    API_KEY_HEADER: str
    AUTHORIZATION_HEADER: str
    CACHE_PREFIX: str
    BEARER_TOKEN_PREFIX: str
    cache_service: Incomplete
    encryption_manager: Incomplete
    def __init__(self, cache_service: CacheService | None) -> None: ...
    def mint_headers(self, access_token: AccessToken) -> dict[str, Any]:
        """Return BOSA-compliant headers derived from the upstream access token."""
