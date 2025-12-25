from bosa_server_plugins.twitter.auth.auth import TwitterClient as TwitterClient
from bosa_server_plugins.twitter.exception.exception import TwitterException as TwitterException
from bosa_server_plugins.twitter.requests.tweets import GetTweetsRequest as GetTweetsRequest, TweetsRequest as TweetsRequest
from bosa_server_plugins.twitter.requests.users import GetUsersRequest as GetUsersRequest

def search_recent_tweets(twitter_client: TwitterClient, tweets_request: TweetsRequest) -> dict:
    """Sends a request to the Twitter API to search for recent tweets.

    Args:
        twitter_client (TwitterClient): The client object for accessing the Twitter API.
        tweets_request (TweetsRequest): The request object containing parameters for the search.

    Raises:
        TwitterException: If the request fails or contains invalid parameters.

    Returns:
        dict: The JSON response from the Twitter API containing the search results, including tweet data and metadata.
    """
def get_multiple_tweet(twitter_client: TwitterClient, get_tweets_request: GetTweetsRequest) -> dict:
    """Sends a request to the Twitter API to retrieve multiple tweets by their IDs.

    Args:
        twitter_client (TwitterClient): The authentication object for accessing the Twitter API.
        get_tweets_request (GetTweetsRequest): The request object containing a list of tweet IDs and optional fields.

    Raises:
        TwitterException: If the request fails or contains invalid parameters.

    Returns:
        dict: The JSON response from the Twitter API containing the requested tweets.
    """
def get_users(twitter_client: TwitterClient, request: GetUsersRequest):
    """Fetch users from Twitter API.

    Args:
        twitter_client (TwitterClient): The authentication object for accessing the Twitter API.
        request (GetUsersRequest): The request object containing parameters to fetch the users.

    Raises:
        TwitterException: If the request fails or contains invalid parameters.

    Returns:
        A dictionary containing information about the users returned by the Twitter API.
    """
