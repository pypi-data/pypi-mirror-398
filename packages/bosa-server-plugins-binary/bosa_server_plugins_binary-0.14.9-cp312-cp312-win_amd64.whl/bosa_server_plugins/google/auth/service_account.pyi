from _typeshed import Incomplete
from bosa_core import ConfigService
from bosa_server_plugins.google.auth.auth import GoogleCredentials as GoogleCredentials
from google.oauth2.credentials import Credentials as Credentials
from typing import Any

class ServiceAccountGoogleCredentials(GoogleCredentials):
    """Google authentication scheme using service account."""
    config: Incomplete
    scopes: Incomplete
    def __init__(self, config: ConfigService | dict[str, Any], scopes: list[str]) -> None:
        """Initialize Google Service Account authentication scheme.

        Args:
            config (ConfigService): The config service
            scopes (list[str]): The scopes
        """
    def get_credentials(self) -> Credentials:
        """Get the credentials.

        Returns:
            Credentials: The credentials
        """
    def to_json(self) -> str:
        """Serialize the service account Google credentials to JSON string.

        Returns:
            str: JSON representation of the service account Google credentials
        """
    @classmethod
    def from_json(cls, json_str: str, config: ConfigService | dict[str, Any]) -> ServiceAccountGoogleCredentials:
        """Deserialize service account Google credentials from JSON string.

        Args:
            json_str: JSON string representation
            config: ConfigService or dict[str, Any] instance

        Returns:
            ServiceAccountGoogleCredentials: The deserialized service account Google credentials
        """
