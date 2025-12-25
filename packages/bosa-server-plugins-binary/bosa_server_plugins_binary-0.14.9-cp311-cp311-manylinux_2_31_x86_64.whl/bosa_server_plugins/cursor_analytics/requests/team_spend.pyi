from bosa_server_plugins.handler.model import BaseRequestModel as BaseRequestModel
from typing import Literal

class TeamSpendRequest(BaseRequestModel):
    """Request model for getting team spending data."""
    search_term: str | None
    sort_by: Literal['amount', 'date', 'user'] | None
    sort_direction: Literal['asc', 'desc'] | None
    page: int | None
    page_size: int | None
