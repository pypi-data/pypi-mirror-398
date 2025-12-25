from _typeshed import Incomplete
from bosa_server_plugins.github.constant import DEFAULT_ITEM_PER_PAGE as DEFAULT_ITEM_PER_PAGE, DEFAULT_PAGE as DEFAULT_PAGE, GITHUB_DATE_FORMAT as GITHUB_DATE_FORMAT, MAXIMUM_ITEM_PER_PAGE as MAXIMUM_ITEM_PER_PAGE, MINIMUM_ITEM_PER_PAGE as MINIMUM_ITEM_PER_PAGE
from bosa_server_plugins.github.gql.common import GQLDirection as GQLDirection
from bosa_server_plugins.github.gql.issue import GQLIssueFilter as GQLIssueFilter, GQLIssueOrderBy as GQLIssueOrderBy
from bosa_server_plugins.github.helper.issues import IssueFields as IssueFields, IssueOrderBy as IssueOrderBy, IssueState as IssueState
from bosa_server_plugins.github.helper.model.common import Direction as Direction, IssueCommentOrderField as IssueCommentOrderField
from bosa_server_plugins.github.requests.common import GithubCursorListRequest as GithubCursorListRequest, validate_fields_datetime_iso_8601 as validate_fields_datetime_iso_8601
from bosa_server_plugins.github.requests.repositories import BasicRepositoryRequest as BasicRepositoryRequest
from bosa_server_plugins.handler import BaseRequestModel as BaseRequestModel
from typing import Literal

class CreateIssueRequest(BasicRepositoryRequest):
    """Request model for creating an issue."""
    title: str
    body: str | None
    assignees: list[str] | None
    milestone: int | None
    labels: list[str] | None

class GQLListIssuesRequest(GithubCursorListRequest, BasicRepositoryRequest):
    """Request model for listing issues."""
    order_by: GQLIssueOrderBy | None
    direction: GQLDirection | None
    filter_by: GQLIssueFilter | None

class GetIssueRequest(BasicRepositoryRequest):
    """Request model for getting an issue."""
    issue_number: int

class GetIssueCommentsRequest(GetIssueRequest):
    """Request model for getting an issue."""
    force_new: bool | None
    created_at_from: str | None
    created_at_to: str | None
    updated_at_from: str | None
    updated_at_to: str | None
    per_page: int | None
    page: int | None
    order_by: IssueCommentOrderField | None
    direction: Direction | None
    def validate_dates(self):
        """Validate date format."""

class AddIssueCommentRequest(GetIssueRequest):
    """Request model for adding an issue comment."""
    body: str

class SearchIssuesRequest(BaseRequestModel):
    """Request model for searching issues."""
    repositories: list[str] | None
    state: IssueState | None
    creator: str | None
    fields: list[IssueFields] | None
    summarize: bool | None
    sort: IssueOrderBy | None
    direction: Direction | None
    labels: list[str] | None
    assignee: str | None
    milestone: int | None
    since: str | None
    until: str | None
    callback_urls: list[str] | None
    waiting: bool | None
    def validate_dates(self):
        """Validate date format."""

SearchSortOptions: Incomplete

class GithubSearchIssuePrRequest(BaseRequestModel):
    """Request model for github search issues and pull request."""
    query: str
    sort: SearchSortOptions | None
    order: Literal['asc', 'desc'] | None
    page: int | None
    per_page: int | None
