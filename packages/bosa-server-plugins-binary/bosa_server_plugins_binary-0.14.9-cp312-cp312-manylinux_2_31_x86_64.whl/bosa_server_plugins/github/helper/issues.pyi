from .pagination import create_github_pagination_meta as create_github_pagination_meta
from bosa_core.cache import CacheService
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.background_task.utils import is_worker_available as is_worker_available
from bosa_server_plugins.common.cache import deserialize_cache_data as deserialize_cache_data, serialize_cache_data as serialize_cache_data
from bosa_server_plugins.github.constant import GITHUB_ISSUES_CACHE_KEY as GITHUB_ISSUES_CACHE_KEY, GITHUB_ISSUES_DEFAULT_TTL as GITHUB_ISSUES_DEFAULT_TTL, MAXIMUM_ITEM_PER_PAGE as MAXIMUM_ITEM_PER_PAGE
from bosa_server_plugins.github.entities.issue import Issue as Issue
from bosa_server_plugins.github.entities.response import GithubAPIResponse as GithubAPIResponse
from bosa_server_plugins.github.helper.common import convert_to_datetime as convert_to_datetime, get_repository_objects as get_repository_objects, get_sanitized_page as get_sanitized_page, get_sanitized_per_page as get_sanitized_per_page, resolve_repositories as resolve_repositories
from bosa_server_plugins.github.helper.connect import send_request_to_github as send_request_to_github
from bosa_server_plugins.github.helper.model.common import Direction as Direction, IssueCommentOrderField as IssueCommentOrderField
from bosa_server_plugins.github.tasks.search_issues_task import CORE_FIELDS as CORE_FIELDS, IssueFields as IssueFields, IssueOrderBy as IssueOrderBy, IssueState as IssueState, create_search_issue_key as create_search_issue_key, create_search_issue_project_details_key as create_search_issue_project_details_key, fetch_repo_issues_data as fetch_repo_issues_data, process_repo_issues as process_repo_issues
from celery.result import AsyncResult as AsyncResult
from typing import Any

GITHUB_ISSUE_COMMENT_CACHE_KEY: str
GITHUB_ISSUE_COMMENT_CACHE_TTL: int

async def get_issue(owner: str, repo: str, issue_number: int, auth_scheme: AuthenticationScheme) -> GithubAPIResponse:
    """Get an issue in a repository.

    Args:
        owner (str): The account owner of the repository
        repo (str): The name of the repository
        issue_number (int): The issue number
        auth_scheme (AuthenticationScheme): Authentication scheme to use

    Returns:
        GithubAPIResponse: The response data, status code and headers
    """
async def get_issues(owner: str, repo: str, auth_scheme: AuthenticationScheme, *, milestone: str | None = None, state: IssueState | None = None, assignee: str | None = None, creator: str | None = None, mentioned: str | None = None, labels: str | None = None, sort: str | None = None, direction: str | None = None, since: str | None = None, per_page: int | None = None, page: int | None = None) -> tuple[list[Issue], dict]:
    """Get all issues in a repository.

    Args:
        owner: The account owner of the repository
        repo: The name of the repository
        auth_scheme: Authentication scheme to use
        milestone: Only issues with the specified milestone are returned
        state: Only issues with the specified state are returned
        assignee: Only issues assigned to the specified user are returned
        creator: Only issues created by the specified user are returned
        mentioned: Only issues mentioning the specified user are returned
        labels: Only issues with the specified labels are returned
        sort: How to sort the issues. Options are: created, updated, popularity, long-running
        direction: The sort direction. Options are: asc, desc
        since: Only issues updated at or after this time are returned
        per_page: Number of issues to return per page
        page: Page number

    Returns:
        List of Issue objects containing issue information
    """
async def get_issue_comments(owner: str, repo: str, issue_number: int, auth_scheme: AuthenticationScheme, *, force_new: bool = False, created_at_from: str | None = None, created_at_to: str | None = None, updated_at_from: str | None = None, updated_at_to: str | None = None, per_page: int | None = None, page: int | None = None, cache_service: CacheService, order_by: IssueCommentOrderField | None = None, direction: Direction | None = None) -> tuple[list[Any], dict]:
    """Get all comments on an issue in a repository.

    Args:
        owner: The account owner of the repository
        repo: The name of the repository
        issue_number: The issue number
        auth_scheme: Authentication scheme to use
        force_new: Whether to force a new request to the API
        created_at_from: Only comments created at or after this time are returned
        created_at_to: Only comments created at or before this time are returned
        updated_at_from: Only comments updated at or after this time are returned
        updated_at_to: Only comments updated at or before this time are returned
        per_page: Number of comments to return per page
        page: Page number,
        cache_service: The cache service to use
        order_by: Field to order comments by (created_at or updated_at). Defaults to CREATED_AT if None.
        direction: Direction to order comments (asc or desc). Defaults to DESC if None.

    Returns:
        List of Issue Comments and pagination metadata
    """
async def add_issue_comment(owner: str, repo: str, issue_number: int, auth_scheme: AuthenticationScheme, *, body: str) -> dict[str, Any]:
    """Add a comment to an issue in a repository.

    Args:
        owner: The account owner of the repository
        repo: The name of the repository
        issue_number: The issue number
        auth_scheme: Authentication scheme to use
        body: The comment body

    Returns:
        The comment object
    """
async def create_issue(owner: str, repo: str, auth_scheme: AuthenticationScheme, title: str, body: str | None = None, assignees: list[str] | None = None, labels: list[str] | None = None, milestone: int | None = None) -> Issue:
    """Create a new issue in a repository.

    Args:
        owner: The account owner of the repository
        repo: The name of the repository
        auth_scheme: Authentication scheme to use
        title: The title of the issue
        body: The body of the issue
        assignees: The assignees of the issue
        labels: The labels of the issue
        milestone: The milestone of the issue

    Returns:
        Issue object containing the created issue information
    """
async def search_issues(auth_scheme: AuthenticationScheme, cache_service: CacheService, *, repositories: list[str] | None = None, since: str | None = None, until: str | None = None, state: IssueState | None = None, creator: str | None = None, fields: list[IssueFields] | None = None, summarize: bool | None = False, sort: IssueOrderBy | None = None, direction: Direction | None = None, labels: list[str] | None = None, assignee: str | None = None, milestone: int | None = None, callback_urls: list[str] | None = None, waiting: bool | None = None) -> tuple | None:
    """Search for issues in repositories.

    Args:
        auth_scheme (AuthenticationScheme): Authentication scheme to use
        cache_service (CacheService): Cache service to use
        repositories (list[str] | None): List of repositories to search in
        since (str | None, optional): Only issues updated at or after this time are returned
        until (str | None, optional): Only issues updated at or before this time are returned
        state (IssueState | None, optional): Only issues with the specified state are returned
        creator (str | None, optional): Only issues created by the specified user are returned
        fields (list[IssueFields] | None, optional): List of fields to include in the response
        summarize (bool | None, optional): Control the level of detail in the results
        sort (IssueOrderBy | None, optional): Sort issues by creation or update time
        direction (Direction | None, optional): Sort direction (asc or desc)
        labels (list[str] | None, optional): Only issues with the specified labels are returned
        assignee (str | None, optional): Only issues assigned to the specified user are returned
        milestone (int | None, optional): Only issues with the specified milestone are returned
        callback_urls (list[str] | None, optional): List of callback URLs to include in the response
        waiting (bool | None, optional): If True, wait for completion. If False/None, run in background.

    Returns:
        tuple | None: Tuple containing list of issues and meta (total count, summary) or None if result is
            still being processed.
    """
