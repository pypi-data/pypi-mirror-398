from bosa_server_plugins.handler.model import BaseRequestModel as BaseRequestModel

class SeatInfoRequest(BaseRequestModel):
    """Request model for getting Copilot seat information."""
    page: int | None
    per_page: int | None
