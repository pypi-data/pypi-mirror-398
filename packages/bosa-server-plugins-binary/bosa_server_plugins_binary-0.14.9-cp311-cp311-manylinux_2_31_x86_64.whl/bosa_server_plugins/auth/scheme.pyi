import abc
from abc import ABC, abstractmethod

class AuthenticationScheme(ABC, metaclass=abc.ABCMeta):
    """Base authentication scheme."""
    @abstractmethod
    def get_token(self) -> str:
        """Get the token.

        Returns:
            str: The token
        """
    @abstractmethod
    def to_headers(self) -> dict[str, str]:
        """Converts the authentication scheme to headers to inject into the request.

        Returns:
            dict: Headers to inject into the request
        """
    @abstractmethod
    def to_json(self) -> str:
        """Serialize the authentication scheme to JSON string.

        Returns:
            str: JSON representation of the authentication scheme
        """
    @classmethod
    def from_json(cls, json_str: str) -> AuthenticationScheme:
        """Deserialize authentication scheme from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            AuthenticationScheme: The deserialized authentication scheme
        """
