from bosa_core.exception import BosaException

class TwitterException(BosaException):
    """Exception raised when Twitter API returns an error."""
    def __init__(self, validation_message: str) -> None:
        """Initialize the exception with field validation details.

        Args:
            validation_message (str): The validation requirement message.
        """
