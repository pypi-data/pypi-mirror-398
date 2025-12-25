from _typeshed import Incomplete
from bosa_server_plugins.auth.bearer import BearerTokenAuthentication as BearerTokenAuthentication
from bosa_server_plugins.github_copilot_analytics.requests.add_user import AddUserRequest as AddUserRequest
from bosa_server_plugins.github_copilot_analytics.requests.remove_user import RemoveUserRequest as RemoveUserRequest
from bosa_server_plugins.github_copilot_analytics.requests.seat_info import SeatInfoRequest as SeatInfoRequest
from bosa_server_plugins.github_copilot_analytics.services.github_copilot_api import GithubCopilotApiService as GithubCopilotApiService
from bosa_server_plugins.handler.header import ExposedDefaultHeaders as ExposedDefaultHeaders
from bosa_server_plugins.handler.router import Router as Router
from typing import Callable

class GithubCopilotAnalyticsRoutes:
    """Routes for GitHub Copilot Analytics endpoints."""
    router: Incomplete
    get_auth_and_organization: Incomplete
    def __init__(self, router: Router, get_auth_and_organization: Callable[[ExposedDefaultHeaders], tuple[BearerTokenAuthentication, str]]) -> None:
        """Initialize GitHub Copilot Analytics routes.

        Args:
            router: The router instance
            get_auth_and_organization: Function to get authentication scheme and organization name
        """
