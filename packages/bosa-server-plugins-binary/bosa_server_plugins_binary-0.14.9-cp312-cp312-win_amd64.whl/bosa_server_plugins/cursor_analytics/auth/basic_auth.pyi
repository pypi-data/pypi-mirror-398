from _typeshed import Incomplete
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme

class BasicAuthAuthentication(AuthenticationScheme):
    """Basic authentication for Cursor API using API key."""
    api_key: Incomplete
    def __init__(self, api_key: str) -> None:
        """Initialization.

        Args:
            api_key: The API key to use for Basic Auth (as username)
        """
    def get_api_key(self) -> str:
        """Get the API key.

        Returns:
            str: The API key
        """
    def get_token(self) -> str:
        """Get the token (API key for Basic Auth).

        Returns:
            str: The API key used as the token
        """
    def to_headers(self) -> dict[str, str]:
        """Converts the authentication scheme to headers.

        Cursor API uses Basic Auth with API key as username and empty password.

        Returns:
            dict: Headers with Authorization Basic Auth
        """
    def to_json(self) -> str:
        """Serialize the basic auth authentication to JSON string.

        Returns:
            str: JSON representation of the basic auth authentication
        """
    @classmethod
    def from_json(cls, json_str: str) -> BasicAuthAuthentication:
        """Deserialize basic auth authentication from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            BasicAuthAuthentication: The deserialized basic auth authentication
        """
