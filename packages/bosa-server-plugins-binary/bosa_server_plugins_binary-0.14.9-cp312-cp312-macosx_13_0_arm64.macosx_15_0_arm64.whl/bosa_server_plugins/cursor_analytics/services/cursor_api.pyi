from _typeshed import Incomplete
from bosa_server_plugins.cursor_analytics.auth.basic_auth import BasicAuthAuthentication as BasicAuthAuthentication
from typing import Any

class CursorApiService:
    """Service for making requests to Cursor API."""
    DEFAULT_TIMEOUT: int
    auth_scheme: Incomplete
    api_url: Incomplete
    def __init__(self, auth_scheme: BasicAuthAuthentication, api_url: str) -> None:
        """Initialize the Cursor API service.

        Args:
            auth_scheme: The authentication scheme
            api_url: The base URL for Cursor API
        """
    async def get_daily_usage_data(self, start_date: int, end_date: int) -> dict[str, Any]:
        """Get daily usage data from Cursor API.

        Args:
            start_date: Start date timestamp in milliseconds
            end_date: End date timestamp in milliseconds

        Returns:
            Dictionary containing daily usage data

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If the request fails
        """
    async def get_team_spend(self, search_term: str | None = None, sort_by: str | None = None, sort_direction: str | None = None, page: int | None = None, page_size: int | None = None) -> dict[str, Any]:
        """Get team spending data from Cursor API.

        Args:
            search_term: Search within user names and emails
            sort_by: Sort by amount, date, or user. Defaults to date
            sort_direction: Sort direction, either asc or desc. Defaults to desc
            page: Page number (1-indexed). Defaults to 1
            page_size: Number of results per page

        Returns:
            Dictionary containing team spending data

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If the request fails
        """
