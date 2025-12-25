from bosa_server_plugins.github.constant import DEFAULT_ITEM_PER_PAGE as DEFAULT_ITEM_PER_PAGE, MAXIMUM_ITEM_PER_PAGE as MAXIMUM_ITEM_PER_PAGE, MINIMUM_ITEM_PER_PAGE as MINIMUM_ITEM_PER_PAGE
from bosa_server_plugins.handler import BaseRequestModel as BaseRequestModel
from datetime import datetime
from pydantic import BaseModel as BaseModel

class GithubCursorListRequest(BaseRequestModel):
    """Request model for listing items with pagination."""
    per_page: int | None
    cursor: str | None
    from_last: bool | None

def validate_fields_datetime_iso_8601(obj: BaseModel, fields: list[str]):
    """Validate fields datetime format.

    Args:
        obj (BaseModel): The model to validate.
        fields (list[str]): The fields to validate.

    Raises:
        ValueError: If any of the fields are not in ISO 8601 format.
    """
def validate_date_format(date: str | None) -> datetime | None:
    """Validate date format.

    Args:
        date (str | None): The date to validate.

    Returns:
        datetime | None: The validated date.

    Raises:
        ValueError: If the date is not in ISO 8601 format.
    """
