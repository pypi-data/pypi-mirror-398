from .pagination import create_github_pagination_meta as create_github_pagination_meta
from bosa_core.cache import CacheService
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.background_task.utils import is_worker_available as is_worker_available
from bosa_server_plugins.common.cache import deserialize_cache_data as deserialize_cache_data, serialize_cache_data as serialize_cache_data
from bosa_server_plugins.github.constant import GITHUB_PULL_REQUESTS_CACHE_KEY as GITHUB_PULL_REQUESTS_CACHE_KEY, GITHUB_PULL_REQUESTS_DEFAULT_TTL as GITHUB_PULL_REQUESTS_DEFAULT_TTL
from bosa_server_plugins.github.entities.response import GithubAPIResponse as GithubAPIResponse
from bosa_server_plugins.github.helper.common import get_repository_objects as get_repository_objects, get_sanitized_page as get_sanitized_page, get_sanitized_per_page as get_sanitized_per_page, resolve_repositories as resolve_repositories
from bosa_server_plugins.github.helper.connect import send_request_to_github as send_request_to_github
from bosa_server_plugins.github.helper.model.common import Direction as Direction
from bosa_server_plugins.github.tasks.search_pull_requests_task import PrOrderBy as PrOrderBy, PrState as PrState, PullRequestFields as PullRequestFields, create_search_pull_request_key as create_search_pull_request_key, create_search_pull_request_project_details_key as create_search_pull_request_project_details_key, fetch_repo_pull_requests_data as fetch_repo_pull_requests_data, process_repo_pull_requests as process_repo_pull_requests
from celery.result import AsyncResult as AsyncResult
from typing import Any

async def get_pull_requests(owner: str, repo: str, auth_scheme: AuthenticationScheme, *, state: str | None = None, head: str | None = None, base: str | None = None, sort: str | None = None, direction: str | None = None, per_page: int | None = None, page: int | None = None) -> tuple[list[Any], Any]:
    """Lists the pull requests of a repository.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        auth_scheme: The authentication scheme.
        state: The state of the pull requests. Can be either 'open', 'closed' or 'all'.
        head: The head branch.
        base: The base branch.
        sort: The sort order. Can be 'created', 'updated', 'popularity' or 'long-running'.
        direction: The sort direction. Can be 'asc' or 'desc'.
        per_page: The number of pull requests to return per page.
        page: The page number.

    Returns:
        tuple[List[Any], Any]: A tuple containing:
        - List[PullRequest]: The list of pull requests.
        - Any: The pagination metadata.
    """
async def search_pull_requests(auth_scheme: AuthenticationScheme, cache_service: CacheService, *, repositories: list[str] | None = None, merged: bool | None = None, draft: bool | None = None, author: str | None = None, labels: list[str] | None = None, since: str | None = None, until: str | None = None, state: PrState | None = None, sort: PrOrderBy | None = None, direction: Direction | None = None, fields: list[PullRequestFields] | None = None, summarize: bool | None = False, callback_urls: list[str] | None = None, waiting: bool | None = None) -> tuple | None:
    """Search for pull requests in a repository.

    Args:
        auth_scheme (AuthenticationScheme): The authentication scheme
        cache_service (CacheService): The cache service
        repositories (list[str] | None, optional): List of repositories to search
        merged (bool | None, optional): Whether to filter for merged pull requests
        draft (bool | None, optional): Whether to filter for draft pull requests
        author (str | None, optional): GitHub login of the PR author
        labels (list[str] | None, optional): List of labels to filter by
        since (str | None, optional): Start date for created date filter
        until (str | None, optional): End date for created date filter
        state (PrState | None, optional): The state of the pull requests. Can be either 'open', 'closed' or 'all'.
        sort (PrOrderBy | None, optional): The sort order. Can be 'created', 'updated', 'popularity' or 'long-running'.
        direction (Direction | None, optional): The sort direction. Can be 'asc' or 'desc'.
        fields (list[PullRequestFields] | None, optional): Optional list of fields to include in the output
        summarize (bool | None, optional): Whether to include summary information
        callback_urls (list[str] | None, optional): List of callback URLs for background processing
        waiting (bool | None, optional): If True, wait for completion. If False/None, run in background.

    Returns:
        tuple | None: Tuple containing list of pull requests and meta (total count, summary) or None if result is
            still being processed.
    """
async def get_pull_request(owner: str, repo: str, pull_number: int, auth_scheme: AuthenticationScheme) -> GithubAPIResponse:
    """Get on pull request data of a repository.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        pull_number: The pull request number.
        auth_scheme: The authentication scheme.

    Returns:
        GithubAPIResponse: The response data, status code and headers
    """
