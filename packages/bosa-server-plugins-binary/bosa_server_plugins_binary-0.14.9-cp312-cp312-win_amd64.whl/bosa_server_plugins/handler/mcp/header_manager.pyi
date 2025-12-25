from _typeshed import Incomplete
from bosa_server_plugins.handler.mcp.auth.bosa_token_mapper import BosaTokenMapper as BosaTokenMapper
from fastapi import Request as Request
from fastmcp import Context as Context
from typing import Any

logger: Incomplete
BOSA_HEADERS_STATE_KEY: str

def safe_get_access_token() -> Any | None:
    """Return the active FastMCP access token if it exists."""
def has_api_key(headers: dict[str, Any]) -> bool:
    """Check whether the headers contain a populated API key."""
def process_colon_separated_api_key(headers: dict[str, Any]) -> dict[str, Any]:
    """Split colon-separated API keys into API key plus Authorization header."""
def to_snake_case_header_dict(headers: dict[str, Any]) -> dict[str, Any]:
    """Return a lowercase snake_case copy of header keys."""

class BosaHeaderManager:
    """Handle minting and caching of BOSA headers for MCP requests."""
    def __init__(self, token_mapper: BosaTokenMapper | None = None) -> None:
        """Initialize the manager.

        Args:
            token_mapper (BosaTokenMapper | None, optional): Mapper used to mint headers from OAuth tokens.
                Defaults to None.
        """
    def ensure_headers(self, base_headers: dict[str, Any] | None, *, access_token: Any | None = None, ctx: Context | None = None, request: Request | None = None, enable_cache: bool = True) -> dict[str, Any]:
        """Return headers enriched with BOSA credentials when required.

        Args:
            base_headers (dict[str, Any] | None): Incoming headers from the FastMCP request.
            access_token (Any | None, optional): FastMCP access token. Defaults to None.
            ctx (Context | None, optional): FastMCP context for the tool invocation. Defaults to None.
            request (Request | None, optional): Underlying FastAPI request when available. Defaults to None.
            enable_cache (bool, optional): Whether to persist headers across calls. Defaults to True.

        Returns:
            dict[str, Any]: Headers guaranteed to include either an API key or freshly minted credentials.
        """
