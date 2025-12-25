from bosa_server_plugins.common.auth.custom import CustomAuthenticationScheme as CustomAuthenticationScheme
from bosa_server_plugins.common.auth.oauth2 import OAuth2AuthenticationScheme as OAuth2AuthenticationScheme
from pydantic import BaseModel, Field as Field, model_serializer
from typing import Annotated, Any

class PluginAuthenticationSchemeResponse(BaseModel):
    """Response model for plugin authentication schemes."""
    supported_auth_types: list[Annotated[CustomAuthenticationScheme | OAuth2AuthenticationScheme, None]]
    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Serialize the model based on the type."""
