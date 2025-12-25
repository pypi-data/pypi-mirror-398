from _typeshed import Incomplete
from bosa_core.exception import BosaException
from enum import Enum

class BosaOAuth2ErrorEnum(Enum):
    """OAuth2 error enum."""
    INVALID_REQUEST = 'invalid_request'
    INTEGRATION_ERROR = 'integration_error'
    CANCELLED_ERROR = 'cancelled_error'
    USER_DUPLICATE_ERROR = 'duplicate_user_error'

class OAuth2CallbackException(BosaException):
    """Exception raised during OAuth2 callback processing with callback URL context."""
    error: Incomplete
    callback_url: Incomplete
    def __init__(self, error: BosaOAuth2ErrorEnum, callback_url: str) -> None:
        """Initialize the exception with original error and callback URL.

        Args:
            error: The error that occurred
            callback_url: The callback URL to redirect to with error information
        """

class InvalidOAuth2StateException(BosaException):
    """Exception raised when state is invalid."""
    def __init__(self) -> None:
        """Initialize the exception."""

class IntegrationExistsException(BosaException):
    """Exception raised when an integration already exists for a user and client."""
    def __init__(self, plugin_name: str, user_id: str) -> None:
        """Initialize the exception with the plugin name.

        Args:
            plugin_name (str): The name of the plugin that already exists.
            user_id (str): The user ID associated with the existing integration.
        """

class IntegrationDoesNotExistException(BosaException):
    """Raised when an integration or account does not exist for the requested connector."""
    def __init__(self, plugin_name: str, user_id: str = 'DEFAULT') -> None:
        '''Create the exception.

        Args:
            plugin_name (str): Connector / plugin name (e.g. "github").
            user_id (str): Account identifier or "DEFAULT" for the default account.
        '''
