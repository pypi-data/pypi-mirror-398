from _typeshed import Incomplete
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme

class BearerTokenAuthentication(AuthenticationScheme):
    """Bearer authentication for Github."""
    token: Incomplete
    def __init__(self, token: str) -> None:
        """Initialization.

        Args:
            token: The bearer token
        """
    def get_token(self) -> str:
        """The bearer token.

        Returns:
            str: The bearer token
        """
    def to_headers(self) -> dict[str, str]:
        """Converts the authentication scheme to headers to inject into the request.

        Returns:
            dict: Headers to inject into the request
        """
    def to_json(self) -> str:
        """Serialize the bearer token authentication to JSON string.

        Returns:
            str: JSON representation of the bearer token authentication
        """
    @classmethod
    def from_json(cls, json_str: str) -> BearerTokenAuthentication:
        """Deserialize bearer token authentication from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            BearerTokenAuthentication: The deserialized bearer token authentication
        """
