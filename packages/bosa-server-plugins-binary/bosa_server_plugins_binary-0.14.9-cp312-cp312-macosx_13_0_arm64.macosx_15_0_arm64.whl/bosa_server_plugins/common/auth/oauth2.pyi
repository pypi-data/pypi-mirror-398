from bosa_server_plugins.common.auth.auth import PluginAuthenticationScheme as PluginAuthenticationScheme
from typing import Literal

class OAuth2AuthenticationScheme(PluginAuthenticationScheme):
    """OAuth2 authentication scheme."""
    type: Literal['oauth2']
