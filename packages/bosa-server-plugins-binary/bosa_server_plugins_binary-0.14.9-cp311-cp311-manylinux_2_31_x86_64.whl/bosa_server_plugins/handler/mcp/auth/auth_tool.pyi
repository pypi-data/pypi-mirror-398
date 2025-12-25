from bosa_server_plugins.common.plugin import ThirdPartyIntegrationPlugin as ThirdPartyIntegrationPlugin
from bosa_server_plugins.common.requests import CustomConfigurationRequest as CustomConfigurationRequest, Oauth2AuthorizationRequest as Oauth2AuthorizationRequest
from bosa_server_plugins.handler import ExposedDefaultHeaders as ExposedDefaultHeaders
from bosa_server_plugins.handler.mcp.auth.bosa_token_mapper import BosaTokenMapper as BosaTokenMapper
from bosa_server_plugins.handler.mcp.header_manager import BosaHeaderManager as BosaHeaderManager, safe_get_access_token as safe_get_access_token, to_snake_case_header_dict as to_snake_case_header_dict
from fastmcp import FastMCP as FastMCP
from pydantic import Field as Field, create_model as create_model

def initialize_authentication_tool(mcp: FastMCP, plugin: ThirdPartyIntegrationPlugin, token_mapper: BosaTokenMapper | None = None) -> None:
    """Initialize the authentication tool for the plugin.

    Args:
        mcp (FastMCP): The MCP instance to inject the tool into.
        plugin (ThirdPartyIntegrationPlugin): The plugin instance.
        token_mapper (BosaTokenMapper | None, optional): Mapper to mint BOSA headers. Defaults to None.
    """
