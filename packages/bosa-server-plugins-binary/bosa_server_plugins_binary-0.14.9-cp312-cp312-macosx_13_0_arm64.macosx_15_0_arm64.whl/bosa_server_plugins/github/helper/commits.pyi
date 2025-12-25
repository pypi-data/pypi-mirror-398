from _typeshed import Incomplete
from bosa_core.cache import CacheService as CacheService
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.background_task.utils import is_worker_available as is_worker_available
from bosa_server_plugins.common.cache import deserialize_cache_data as deserialize_cache_data
from bosa_server_plugins.common.callback import delete_callback_urls as delete_callback_urls, get_callback_urls as get_callback_urls, save_callback_urls as save_callback_urls, with_callbacks as with_callbacks
from bosa_server_plugins.github.constant import AUTH_CACHE_KEY_FORMAT as AUTH_CACHE_KEY_FORMAT, AUTH_CACHE_TTL as AUTH_CACHE_TTL
from bosa_server_plugins.github.entities.commit import CommitSearchContext as CommitSearchContext, SearchFilters as SearchFilters
from bosa_server_plugins.github.helper.common import convert_to_datetime as convert_to_datetime, get_repository_objects as get_repository_objects, get_sanitized_page as get_sanitized_page, get_sanitized_per_page as get_sanitized_per_page, resolve_repositories as resolve_repositories
from bosa_server_plugins.github.tasks.get_all_pr_commits_task import get_all_pr_commits_task as get_all_pr_commits_task, handle_chord_result as handle_chord_result
from bosa_server_plugins.github.utils.commit import generate_search_commit_key as generate_search_commit_key, get_all_cached_data as get_all_cached_data, get_cached_data as get_cached_data, get_wrapped_result as get_wrapped_result
from celery.result import AsyncResult as AsyncResult
from typing import Any

logger: Incomplete

async def search_repository_commits(auth_scheme: AuthenticationScheme, *, repositories: list[str] | None = None, since: str | None = None, until: str | None = None, author: str | None = None, fields: list[str] | None = None, summarize: bool | None = False, per_page: int | None = None, page: int | None = None, cache_service: CacheService | None = None, callback_urls: list[str] | None = None, waiting: bool | None = None) -> tuple[dict[str, Any], list[str]]:
    """Retrieve commits from specified GitHub repositories.

    Main entry point for commit search functionality. Supports searching across multiple
    repositories with filtering by date range and author. Results can be summarized
    and are cached for improved performance.

    Args:
        auth_scheme (AuthenticationScheme): Authentication scheme for GitHub API access.
        repositories (list[str] | None, optional): List of repositories to search. If None, uses all accessible repos.
        since (str | None, optional): Start date for commit search (ISO format string).
        until (str | None, optional): End date for commit search (ISO format string).
        author (str | None, optional): Author of commits to search for.
        fields (list[str] | None, optional): List of fields to extract from commits.
        summarize (bool | None, optional): Whether to summarize results (limit to top 5 commits).
        per_page (int | None, optional): Number of commits per page.
        page (int | None, optional): Page number for pagination.
        cache_service (CacheService | None, optional): Cache service for storing results.
        callback_urls (list[str] | None, optional): List of callback URLs to notify when processing completes.
        waiting (bool | None, optional): If True, wait for completion (sync mode). If False/None, run in background.

    Returns:
        Tuple containing:
            - Dictionary with search results including:
                - repositories: List of processed repositories
                - total_commits: Total number of commits found
                - commits: List of commit details
                - is_processing: Boolean indicating if processing is ongoing
                - author_commit_counts: Optional count of commits by author
            - List of error messages if any occurred

    Raises:
        ValueError: If cache_service is not provided or no repositories could be resolved.
    """
