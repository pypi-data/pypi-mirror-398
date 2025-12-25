from bosa_server_plugins.handler.model import BaseRequestModel as BaseRequestModel

class DailyUsageRequest(BaseRequestModel):
    """Request model for getting daily usage data."""
    start_date: str
    end_date: str
    def validate_dates(self):
        """Validate date format."""
