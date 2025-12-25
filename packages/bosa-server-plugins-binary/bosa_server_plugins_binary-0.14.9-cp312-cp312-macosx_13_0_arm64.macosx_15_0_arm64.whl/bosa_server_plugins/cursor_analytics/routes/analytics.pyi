from _typeshed import Incomplete
from bosa_server_plugins.cursor_analytics.auth.basic_auth import BasicAuthAuthentication as BasicAuthAuthentication
from bosa_server_plugins.cursor_analytics.requests.daily_usage import DailyUsageRequest as DailyUsageRequest
from bosa_server_plugins.cursor_analytics.requests.team_spend import TeamSpendRequest as TeamSpendRequest
from bosa_server_plugins.cursor_analytics.services.cursor_api import CursorApiService as CursorApiService
from bosa_server_plugins.handler.header import ExposedDefaultHeaders as ExposedDefaultHeaders
from bosa_server_plugins.handler.router import Router as Router
from typing import Callable

class CursorAnalyticsRoutes:
    """Routes for Cursor Analytics endpoints."""
    router: Incomplete
    get_auth_scheme: Incomplete
    get_api_url: Incomplete
    def __init__(self, router: Router, get_auth_scheme: Callable[[ExposedDefaultHeaders], BasicAuthAuthentication], get_api_url: Callable[[ExposedDefaultHeaders], str]) -> None:
        """Initialize Cursor Analytics routes.

        Args:
            router: The router instance
            get_auth_scheme: Function to get authentication scheme
            get_api_url: Function to get API URL
        """
