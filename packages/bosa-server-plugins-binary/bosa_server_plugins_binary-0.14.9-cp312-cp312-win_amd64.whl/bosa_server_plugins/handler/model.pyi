from bosa_server_plugins.common.filter import CustomFieldFilter as CustomFieldFilter
from pydantic import BaseModel

class BaseRequestModel(BaseModel):
    """Base model for all requests that enables response field filtering."""
    response_fields: list[str] | None
    response_filters: list[CustomFieldFilter] | None
