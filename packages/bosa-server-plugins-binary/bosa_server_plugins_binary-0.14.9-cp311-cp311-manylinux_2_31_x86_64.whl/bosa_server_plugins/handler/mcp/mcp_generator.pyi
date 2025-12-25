import contextlib
from _typeshed import Incomplete
from bosa_core.cache import CacheService as CacheService
from bosa_server_plugins.handler.mcp.auth.bosa_oauth_proxy import BosaOAuthProxy as BosaOAuthProxy
from bosa_server_plugins.handler.mcp.auth.bosa_token_verifier import BosaTokenVerifier as BosaTokenVerifier
from fastapi import FastAPI as FastAPI
from fastmcp import FastMCP
from fastmcp.server.http import StarletteWithLifespan as StarletteWithLifespan
from typing import Any

class McpGenerator:
    """Create FastMCP instances that share a centralized OAuth app."""
    mcps: dict[str, FastMCP]
    mcp_apps: dict[str, StarletteWithLifespan]
    oauth_mcp: FastMCP | None
    oauth_app: StarletteWithLifespan | None
    cache_service: Incomplete
    google_auth_provider: Any
    def __init__(self, cache_service: CacheService | None = None) -> None:
        """Initialize the generator.

        Args:
            cache_service (CacheService | None, optional): Cache helper used by token mappers.
                Defaults to None.
        """
    def generate_fastmcp(self, plugin_classes: list[type[Any]], mcp_name: str = 'bosa') -> tuple[dict[str, FastMCP], dict[str, StarletteWithLifespan], StarletteWithLifespan | None]:
        '''Return FastMCP apps for the provided plugins.

        Args:
            plugin_classes (list[type[Any]]): Plugin implementations with a `name` attribute.
            mcp_name (str, optional): Common prefix applied to generated MCPs. Defaults to "bosa".

        Returns:
            tuple[dict[str, FastMCP], dict[str, StarletteWithLifespan], StarletteWithLifespan | None]:
                Tuple containing MCP instances, their Starlette apps, and the shared OAuth app.
        '''
    @contextlib.asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Manage FastAPI lifespan events for all generated apps.

        Args:
            app (FastAPI): FastAPI application consuming the MCP apps.

        Yields:
            None: Lifespan context completes when nested apps exit.
        """
