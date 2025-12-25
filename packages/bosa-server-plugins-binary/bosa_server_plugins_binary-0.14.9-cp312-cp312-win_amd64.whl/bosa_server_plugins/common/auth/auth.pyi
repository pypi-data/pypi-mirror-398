from abc import ABC
from pydantic import BaseModel

class PluginAuthenticationScheme(ABC, BaseModel):
    """Base class for plugin authentication schemes."""
    type: str
