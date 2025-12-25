from bosa_server_plugins.common.auth.auth import PluginAuthenticationScheme as PluginAuthenticationScheme
from pydantic import BaseModel as BaseModel
from typing import Literal

class CustomAuthenticationScheme(PluginAuthenticationScheme):
    """Custom authentication scheme."""
    type: Literal['custom']
    config: type[BaseModel]
