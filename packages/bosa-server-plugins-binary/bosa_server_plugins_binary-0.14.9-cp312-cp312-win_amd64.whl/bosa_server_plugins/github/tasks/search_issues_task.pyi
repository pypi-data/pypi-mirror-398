from _typeshed import Incomplete
from bosa_server_plugins.auth.bearer import BearerTokenAuthentication as BearerTokenAuthentication
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.common.cache import deserialize_cache_data as deserialize_cache_data, serialize_cache_data as serialize_cache_data
from bosa_server_plugins.common.callback import with_callbacks as with_callbacks
from bosa_server_plugins.github.constant import GITHUB_ISSUES_CACHE_KEY as GITHUB_ISSUES_CACHE_KEY, GITHUB_ISSUES_DEFAULT_TTL as GITHUB_ISSUES_DEFAULT_TTL
from bosa_server_plugins.github.gql.issue import gql_get_all_issues_project_details as gql_get_all_issues_project_details
from bosa_server_plugins.github.gql.project_details import GQLProjectDetails as GQLProjectDetails
from bosa_server_plugins.github.helper.common import count_items as count_items
from bosa_server_plugins.github.helper.model.common import Direction as Direction
from enum import StrEnum
from typing import Any

class IssueState(StrEnum):
    """REST API issue state model."""
    OPEN = 'open'
    CLOSED = 'closed'
    ALL = 'all'

class IssueOrderBy(StrEnum):
    """REST API issue order by model."""
    CREATED = 'created'
    UPDATED = 'updated'
    COMMENTS = 'comments'

class IssueFields(StrEnum):
    """REST API issue fields model."""
    REPOSITORY = 'repository'
    NUMBER = 'number'
    TITLE = 'title'
    CREATOR = 'creator'
    BODY = 'body'
    STATE = 'state'
    URL = 'url'
    LABELS = 'labels'
    MILESTONE = 'milestone'
    COMMENTS = 'comments'
    ASSIGNEE = 'assignee'
    ASSIGNEES = 'assignees'
    CREATED_AT = 'created_at'
    UPDATED_AT = 'updated_at'
    PROJECT_DETAILS = 'project_details'

CORE_FIELDS: Incomplete

def fetch_repo_issues_data(self, auth_key: str, encrypted_token: str, repository: str, parameters: dict[str, Any], query_project_details: bool = False) -> tuple[str, list[dict[str, Any]], dict[str, dict | None], str | None]:
    """Retrieve issues data (and project details optionally) from a specified GitHub repository.

    Args:
        self: Celery task instance.
        auth_key (str): Authentication key.
        encrypted_token (str): Encrypted token.
        repository (str): GitHub repository name.
        parameters (Dict[str, Any]): Parameters for filtering issues.
        query_project_details (bool): Whether to query project details.

    Returns:
        tuple[str, list[dict[str, Any]], dict[str, dict | None], str | None]: GitHub repository name,
            list of issues data, dict of project details, error message.
    """
def create_search_issue_key(encrypted_token: str, repository: str, parameters: dict[str, Any]) -> str:
    """Create a key for caching issues data.

    Args:
        encrypted_token: Encrypted token.
        repository: GitHub repository name.
        parameters: Parameters for the issues query.

    Returns:
        str: Key for caching issues data.
    """
def create_search_issue_project_details_key(encrypted_token: str, repository: str) -> str:
    """Create a key for caching issues project details data.

    Args:
        encrypted_token: Encrypted token.
        repository: GitHub repository name.

    Returns:
        str: Key for caching issues project details data.
    """
def process_repo_issues(self, results: list[tuple[str, list, dict, str | None]], fields: list[IssueFields], parameters: dict[str, Any], summarize: bool | None, callback_urls: list[str] | None = None) -> tuple[dict[str, Any], list[str] | None]:
    """Process issues data from a specified GitHub repository.

    Args:
        self: Celery task instance.
        results (list[tuple[str, list, dict, str]]): List of tuples containing repository,
            issues, project details, and error.
        fields (list[IssueFields]): List of fields to include in the result.
        parameters (dict[str, Any]): Parameters for the issues query.
        summarize (bool): Whether to summarize issues.
        callback_urls (list[str] | None): List of callback URLs.

    Returns:
        tuple[dict[str, Any], list[str] | None]: Issues data and metadata; with callback URLs.
    """
