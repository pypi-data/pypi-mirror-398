from bosa_server_plugins.github.constant import DEFAULT_ITEM_PER_PAGE as DEFAULT_ITEM_PER_PAGE, DEFAULT_PAGE as DEFAULT_PAGE, MAXIMUM_ITEM_PER_PAGE as MAXIMUM_ITEM_PER_PAGE, MINIMUM_ITEM_PER_PAGE as MINIMUM_ITEM_PER_PAGE
from bosa_server_plugins.github.requests.common import validate_fields_datetime_iso_8601 as validate_fields_datetime_iso_8601
from bosa_server_plugins.handler import BaseRequestModel as BaseRequestModel
from enum import Enum

ORGANIZATION_DESCRIPTION: str
PROJECT_NUMBER_DESCRIPTION: str

class OrderByDirection(str, Enum):
    """Order by direction."""
    ASC = 'asc'
    DESC = 'desc'

class OrderByField(str, Enum):
    """Order by field."""
    CREATED_AT = 'created_at'
    NUMBER = 'number'
    TITLE = 'title'
    UPDATED_AT = 'updated_at'

class ContentType(str, Enum):
    """Content type for project items."""
    ISSUE = 'Issue'
    PULL_REQUEST = 'PullRequest'

class GithubProjectBaseRequest(BaseRequestModel):
    """Github Projects V2 Base Request."""
    organization: str
    number: int
    per_page: int | None
    page: int | None
    force_new: bool | None

class GithubListProjectCardsRequest(GithubProjectBaseRequest):
    """Github List Project Cards Request Body."""
    status: str | None
    type: str | None
    created_at_from: str | None
    created_at_to: str | None
    updated_at_from: str | None
    updated_at_to: str | None
    summarize: bool | None
    callback_urls: list[str] | None
    waiting: bool | None
    def validate_dates(self) -> GithubListProjectCardsRequest:
        """Validate that all date fields are in the correct ISO 8601 format."""

class GithubListProjectsRequest(BaseRequestModel):
    """Github List Projects Request Body."""
    organization: str
    query: str | None
    force_new: bool | None
    order_by: OrderByField | None
    direction: OrderByDirection | None
    per_page: int | None
    page: int | None

class GithubAddProjectItemRequest(BaseRequestModel):
    """Github Add Project Item Request Body."""
    organization: str
    project_number: int
    repository: str
    content_type: ContentType
    content_number: int

class GithubGetProjectItemRequest(BaseRequestModel):
    """Github Get Project Item Request Body."""
    organization: str
    project_number: int
    item_id: int
    force_new: bool | None

class FieldUpdate(BaseRequestModel):
    """Single field update for a project item."""
    id: int
    value: str | int | float | None

class GithubUpdateProjectItemRequest(BaseRequestModel):
    """Github Update Project Item Request Body."""
    organization: str
    project_number: int
    item_id: int
    fields: list[FieldUpdate]

class GithubListProjectFieldsRequest(BaseRequestModel):
    """Github List Project Fields Request Body."""
    organization: str
    project_number: int
    per_page: int | None
    before: str | None
    after: str | None
    force_new: bool | None
