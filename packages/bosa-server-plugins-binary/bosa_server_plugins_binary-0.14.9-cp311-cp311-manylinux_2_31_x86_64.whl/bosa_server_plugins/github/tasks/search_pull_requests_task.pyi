from _typeshed import Incomplete
from bosa_server_plugins.auth.bearer import BearerTokenAuthentication as BearerTokenAuthentication
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.common.cache import deserialize_cache_data as deserialize_cache_data, serialize_cache_data as serialize_cache_data
from bosa_server_plugins.common.callback import with_callbacks as with_callbacks
from bosa_server_plugins.github.constant import GITHUB_DATE_FORMAT as GITHUB_DATE_FORMAT, GITHUB_PULL_REQUESTS_CACHE_KEY as GITHUB_PULL_REQUESTS_CACHE_KEY, GITHUB_PULL_REQUESTS_DEFAULT_TTL as GITHUB_PULL_REQUESTS_DEFAULT_TTL
from bosa_server_plugins.github.gql.project_details import GQLProjectDetails as GQLProjectDetails
from bosa_server_plugins.github.gql.pull_request import gql_get_all_pull_request_project_details as gql_get_all_pull_request_project_details
from bosa_server_plugins.github.helper.common import count_items as count_items
from bosa_server_plugins.github.helper.model.common import Direction as Direction
from enum import StrEnum
from typing import Any

class PrState(StrEnum):
    """Pull request state model."""
    OPEN = 'open'
    CLOSED = 'closed'
    ALL = 'all'

class PrOrderBy(StrEnum):
    """Pull request order by model."""
    CREATED = 'created'
    UPDATED = 'updated'
    POPULARITY = 'popularity'
    LONG_RUNNING = 'long-running'

class PullRequestFields(StrEnum):
    """Pull request fields model."""
    REPOSITORY = 'repository'
    NUMBER = 'number'
    TITLE = 'title'
    AUTHOR = 'author'
    BODY = 'body'
    STATE = 'state'
    DRAFT = 'draft'
    URL = 'url'
    LABELS = 'labels'
    MILESTONE = 'milestone'
    ASSIGNEE = 'assignee'
    ASSIGNEES = 'assignees'
    CREATED_AT = 'created_at'
    MERGED_AT = 'merged_at'
    UPDATED_AT = 'updated_at'
    PROJECT_DETAILS = 'project_details'

CORE_FIELDS: Incomplete

def fetch_repo_pull_requests_data(self, auth_key: str, encrypted_token: str, repository: str, parameters: dict[str, Any], query_project_details: bool = False) -> tuple[str, list[dict[str, Any]], dict[str, dict | None], str | None]:
    """Retrieve pull requests data (and project details optionally) from a specified GitHub repository.

    Args:
        self: Celery task instance.
        auth_key: Authentication key.
        encrypted_token: Encrypted token.
        repository: GitHub repository name.
        parameters: Parameters for the pull requests query.
        query_project_details: Whether to query project details.

    Returns:
        tuple[str, list[dict[str, Any]], dict[str, dict | None], str | None]: GitHub repository name,
            list of pull requests data, dict of project details, and error message.
    """
def create_search_pull_request_key(encrypted_token: str, repository: str, parameters: dict[str, Any]) -> str:
    """Create a key for caching pull requests data.

    Args:
        encrypted_token: Encrypted token.
        repository: GitHub repository name.
        parameters: Parameters for the pull requests query.

    Returns:
        str: Key for caching pull requests data.
    """
def create_search_pull_request_project_details_key(encrypted_token: str, repository: str) -> str:
    """Create a key for caching pull requests project details data.

    Args:
        encrypted_token: Encrypted token.
        repository: GitHub repository name.

    Returns:
        str: Key for caching pull requests project details data.
    """
def process_repo_pull_requests(self, results: list[tuple[str, list, dict, str | None]], fields: list[PullRequestFields], parameters: dict[str, Any], summarize: bool, callback_urls: list[str] | None = None) -> tuple[dict[str, Any], list[str] | None]:
    """Process pull requests data from a specified GitHub repository.

    Args:
        self: Celery task instance.
        results (list[tuple[str, list, dict, str | None]]): List of tuples containing repository,
            pull requests, project details, and error.
        fields (list[PullRequestFields]): List of fields to include in the result.
        parameters (dict[str, Any]): Parameters for the pull requests query.
        summarize (bool): Whether to summarize pull requests.
        callback_urls (list[str] | None): List of callback URLs.

    Returns:
        tuple[dict[str, Any], list[str] | None]: Pull requests data and metadata; with callback URLs.
    """
def validate_merged_status(raw_data: dict[str, Any], filters: dict[str, Any]):
    """Validate the merged status of a pull request based on filters.

    Args:
        raw_data: The raw data of the pull request.
        filters: A dictionary of filters to apply.

    Returns:
        bool: True if the PR matches the merged filter, False otherwise.
    """
def validate_draft_status(raw_data: dict[str, Any], filters: dict[str, Any]):
    """Validate the draft status of a pull request based on filters.

    Args:
        raw_data: The raw data of the pull request.
        filters: A dictionary of filters to apply.

    Returns:
        bool: True if the PR matches the draft filter, False otherwise.
    """
def validate_author(raw_data: dict[str, Any], filters: dict[str, Any]):
    """Validate the author of a pull request based on filters.

    Args:
        raw_data: The raw data of the pull request.
        filters: A dictionary of filters to apply.

    Returns:
        bool: True if the PR matches the author filter, False otherwise.
    """
def validate_labels(raw_data: dict[str, Any], filters: dict[str, Any]):
    """Validate the labels of a pull request based on filters.

    Args:
        raw_data: The raw data of the pull request.
        filters: A dictionary of filters to apply.

    Returns:
        bool: True if the PR matches the labels filter, False otherwise.
    """
def validate_date(raw_data: dict[str, Any], filters: dict[str, Any]) -> bool:
    """Validate if a PR matches the date filters.

    Args:
        raw_data: The raw data of the pull request.
        filters: A dictionary of filters to apply.

    Returns:
        bool: True if the PR matches the date filters, False otherwise.
    """
