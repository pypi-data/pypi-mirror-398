from bosa_core import ConfigService as ConfigService
from datetime import datetime
from google.oauth2.credentials import Credentials

class GoogleCredentials:
    """Google authentication scheme."""
    TIMEZONE: str
    token: str
    refresh_token: str
    expiry: datetime
    config: ConfigService
    def __init__(self, token: str, refresh_token: str, expiry: str, config: ConfigService) -> None:
        """Initialize Google authentication scheme.

        Args:
            token (str): The token
            refresh_token (str): The refresh token
            expiry (str): The expiry date
            config (ConfigService): The config service
        """
    def get_credentials(self) -> Credentials:
        """Get the credentials.

        Returns:
            dict: The credentials
        """
    def to_json(self) -> str:
        """Serialize the Google credentials to JSON string.

        Returns:
            str: JSON representation of the Google credentials
        """
    @classmethod
    def from_json(cls, json_str: str, config: ConfigService) -> GoogleCredentials:
        """Deserialize Google credentials from JSON string.

        Args:
            json_str: JSON string representation
            config: ConfigService instance

        Returns:
            GoogleCredentials: The deserialized Google credentials
        """
