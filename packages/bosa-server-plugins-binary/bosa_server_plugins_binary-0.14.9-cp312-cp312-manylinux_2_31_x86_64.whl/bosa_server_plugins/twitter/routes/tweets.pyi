from _typeshed import Incomplete
from bosa_server_plugins.handler import ExposedDefaultHeaders as ExposedDefaultHeaders, Router as Router
from bosa_server_plugins.twitter.auth.auth import TwitterClient as TwitterClient
from bosa_server_plugins.twitter.helpers.connect import get_multiple_tweet as get_multiple_tweet, search_recent_tweets as search_recent_tweets
from bosa_server_plugins.twitter.helpers.tweets import build_tweet_thread as build_tweet_thread
from bosa_server_plugins.twitter.requests.tweets import GetThreadRequest as GetThreadRequest, GetTweetsRequest as GetTweetsRequest, TweetsRequest as TweetsRequest
from typing import Callable

class TweetRoutes:
    """Registers tweet-related endpoints to a FastAPI router.

    This class handles routing for Twitter operations such as searching for tweets
    using the Twitter API. It defines and binds the necessary endpoints when initialized.
    """
    router: Incomplete
    get_auth_scheme: Incomplete
    def __init__(self, router: Router, get_auth_scheme: Callable[[ExposedDefaultHeaders], TwitterClient]) -> None:
        """Initializes the TweetRoutes with a FastAPI router and Twitter API authentication.

        Args:
            router: The router instance to register the routes.
            get_auth_scheme: Function to get the authentication scheme.
        """
