from _typeshed import Incomplete
from bosa_server_plugins.handler import ExposedDefaultHeaders as ExposedDefaultHeaders, Router as Router
from bosa_server_plugins.twitter.auth.auth import TwitterClient as TwitterClient
from bosa_server_plugins.twitter.requests.users import GetUsersRequest as GetUsersRequest
from typing import Callable

class UserRoutes:
    """Class to define user-related routes for the Twitter API."""
    router: Incomplete
    get_auth_scheme: Incomplete
    def __init__(self, router: Router, get_auth_scheme: Callable[[ExposedDefaultHeaders], TwitterClient]) -> None:
        """Initialize UserRoutes with a router and an authentication token.

        Args:
            router: The router instance to register the routes.
            get_auth_scheme: Function to get the authentication scheme.
        """
