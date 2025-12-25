from _typeshed import Incomplete
from bosa_server_plugins.auth.bearer import BearerTokenAuthentication as BearerTokenAuthentication
from bosa_server_plugins.github_copilot_analytics.constants import BASE_API_GITHUB_URL as BASE_API_GITHUB_URL, CURRENT_API_VERSION as CURRENT_API_VERSION, DEFAULT_TIMEOUT as DEFAULT_TIMEOUT
from typing import Any

class GithubCopilotApiService:
    """Service for making requests to GitHub Copilot API."""
    auth_scheme: Incomplete
    def __init__(self, auth_scheme: BearerTokenAuthentication) -> None:
        """Initialize the GitHub Copilot API service.

        Args:
            auth_scheme: The authentication scheme
        """
    async def add_users_to_copilot(self, organization: str, selected_usernames: list[str]) -> dict[str, Any]:
        """Add users to GitHub Copilot subscription.

        Args:
            organization: GitHub organization name
            selected_usernames: List of GitHub usernames to add

        Returns:
            Dictionary containing seats_added count

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If the request fails
        """
    async def remove_users_from_copilot(self, organization: str, selected_usernames: list[str]) -> dict[str, Any]:
        """Remove users from GitHub Copilot subscription.

        Args:
            organization: GitHub organization name
            selected_usernames: List of GitHub usernames to remove

        Returns:
            Dictionary containing seats_cancelled count

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If the request fails
        """
    async def get_copilot_seats(self, organization: str, page: int | None = None, per_page: int | None = None) -> dict[str, Any]:
        """Get Copilot seat assignments for an organization.

        Args:
            organization: GitHub organization name
            page: Page number for pagination
            per_page: Number of items per page

        Returns:
            Dictionary containing seat assignments

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If the request fails
        """
