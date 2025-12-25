from pydantic import BaseModel

class CursorAnalyticsConfig(BaseModel):
    """Configuration for Cursor Analytics integration.

    Attributes:
        api_key (str): Cursor API key for authentication.
        user_identifier (str): The user identifier for the integration.
    """
    api_key: str
    user_identifier: str
