from _typeshed import Incomplete
from bosa_core import Plugin as Plugin
from bosa_core.authentication.token.service import VerifyTokenService as VerifyTokenService
from bosa_core.cache import CacheService as CacheService
from bosa_server_plugins.common.remote.plugin import RemoteServerPlugin as RemoteServerPlugin
from bosa_server_plugins.handler import ExposedDefaultHeaders as ExposedDefaultHeaders, HttpHandler as HttpHandler
from bosa_server_plugins.handler.auth import AuthenticationSchema as AuthenticationSchema
from bosa_server_plugins.handler.fastapi_schema import FastApiSchemaExtractor as FastApiSchemaExtractor
from bosa_server_plugins.handler.header import HttpHeaders as HttpHeaders
from bosa_server_plugins.handler.mcp.auth.auth_tool import initialize_authentication_tool as initialize_authentication_tool
from bosa_server_plugins.handler.mcp.auth.bosa_token_mapper import BosaTokenMapper as BosaTokenMapper
from bosa_server_plugins.handler.mcp.auth.bosa_token_verifier import BosaTokenVerifier as BosaTokenVerifier
from bosa_server_plugins.handler.mcp.header_manager import BosaHeaderManager as BosaHeaderManager, process_colon_separated_api_key as process_colon_separated_api_key, safe_get_access_token as safe_get_access_token, to_snake_case_header_dict as to_snake_case_header_dict
from bosa_server_plugins.handler.mcp.mcp_generator import McpGenerator as McpGenerator
from bosa_server_plugins.handler.response import ApiResponse as ApiResponse
from bosa_server_plugins.handler.router import Router as Router
from bosa_server_plugins.handler.schema import SchemaExtractor as SchemaExtractor
from fastapi import FastAPI as FastAPI, Request as Request
from fastmcp import FastMCP as FastMCP
from fastmcp.server.http import StarletteWithLifespan as StarletteWithLifespan
from pydantic import BaseModel as BaseModel
from pydantic.fields import FieldInfo as FieldInfo

class McpFastApiHandler(HttpHandler):
    """MCP interface for FastAPI with centralized OAuth support."""
    excluded_endpoints: Incomplete
    app: Incomplete
    mcp_name: Incomplete
    mcps: Incomplete
    mcp_apps: Incomplete
    oauth_app: Incomplete
    verify_token_service: Incomplete
    def __init__(self, app: FastAPI, mcps: dict[str, FastMCP], mcp_apps: dict[str, StarletteWithLifespan], oauth_app: StarletteWithLifespan = None, base_api_prefix: str = '/api', authentication_schema: AuthenticationSchema = None, cache_service: CacheService | None = None, mcp_name: str = 'bosa', verify_token_service: VerifyTokenService | None = None) -> None:
        """Initialize the MCP FastAPI interface.

        Args:
            app: The FastAPI app
            mcps: Dictionary mapping plugin names to FastMCP instances
            mcp_apps: Dictionary mapping plugin names to their Starlette apps
            oauth_app: Centralized OAuth app to mount at root (optional)
            base_api_prefix: The base API prefix
            authentication_schema: The authentication schema
            mcp_name: The MCP name
        """
    @classmethod
    def initialize_plugin(cls, instance: HttpHandler, plugin: Plugin) -> None:
        """Initialize HTTP-specific resources for the plugin.

        If the plugin has a router attribute, register its routes with the HTTP interface.
        At the same time, register the plugin's routes for MCP-compliance.

        Args:
            instance: The HTTP interface instance
            plugin: The plugin instance to initialize
        """
    def initialize_mcp(self, plugin: Plugin):
        """Initialize the MCP for the plugin.

        Args:
            plugin: The plugin instance to initialize
        """
    def get_schema_extractor(self) -> SchemaExtractor:
        """Get the schema extractor for this interface.

        Returns:
            SchemaExtractor implementation for this interface
        """
    def handle_routing(self, prefix: str, router: Router):
        """Register routes with the HTTP interface.

        Args:
            prefix: The prefix for the routes
            router: The router instance
        """
