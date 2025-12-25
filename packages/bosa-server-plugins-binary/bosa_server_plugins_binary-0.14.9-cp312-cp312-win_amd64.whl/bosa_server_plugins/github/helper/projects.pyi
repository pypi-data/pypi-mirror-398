from bosa_core.cache import CacheService
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.background_task.utils import is_worker_available as is_worker_available
from bosa_server_plugins.common.cache import serialize_cache_data as serialize_cache_data
from bosa_server_plugins.github.constant import GITHUB_PROJECTS_CACHE_KEY as GITHUB_PROJECTS_CACHE_KEY, GITHUB_PROJECTS_DEFAULT_TTL_IN_SECONDS as GITHUB_PROJECTS_DEFAULT_TTL_IN_SECONDS, MAXIMUM_ITEM_PER_PAGE as MAXIMUM_ITEM_PER_PAGE
from bosa_server_plugins.github.entities.project import Project as Project, ProjectItem as ProjectItem, ProjectListMeta as ProjectListMeta, ProjectListResponse as ProjectListResponse
from bosa_server_plugins.github.helper.common import get_sanitized_page as get_sanitized_page, get_sanitized_per_page as get_sanitized_per_page
from bosa_server_plugins.github.helper.connect import send_request_to_github as send_request_to_github
from bosa_server_plugins.github.helper.issues import get_issue as get_issue
from bosa_server_plugins.github.helper.pull_requests import get_pull_request as get_pull_request
from bosa_server_plugins.github.requests.projects import OrderByDirection as OrderByDirection, OrderByField as OrderByField
from bosa_server_plugins.github.tasks.get_list_project_items_task import GetItemsFromProjectParameter as GetItemsFromProjectParameter, ProjectSummary as ProjectSummary, get_items_from_project_process as get_items_from_project_process, get_items_from_project_task as get_items_from_project_task, process_items_from_project_request as process_items_from_project_request
from celery.result import AsyncResult as AsyncResult
from typing import Any

async def get_project_item(organization: str, project_number: int, item_id: int, auth_scheme: AuthenticationScheme, cache_service: CacheService | None = None, force_new: bool = False) -> dict:
    """Get a specific item from a GitHub Project V2.

    Args:
        organization (str): Organization name.
        project_number (int): Project number.
        item_id (int): The unique identifier of the project item.
        auth_scheme (AuthenticationScheme): Authentication scheme.
        cache_service (CacheService | None, optional): Cache service for caching
            results. Defaults to None.
        force_new (bool, optional): If True, bypass cache and fetch new data.
            Defaults to False.

    Returns:
        dict: The project item data from GitHub REST API.

    Raises:
        HTTPError: If the GitHub API request fails (404 for not found, 403 for
            forbidden).
    """
async def add_item_to_project(organization: str, project_number: int, repository: str, content_number: int, content_type: str, auth_scheme: AuthenticationScheme) -> dict:
    '''Add an item to a GitHub Project V2.

    Args:
        organization: Organization name
        project_number: Project number
        content_id: The global node ID of the Issue/PR
        content_type: Type of content ("Issue" or "PullRequest")
        auth_scheme: Authentication scheme

    Returns:
        dict: The newly added project item data

    Raises:
        HTTPError: If the GitHub API request fails
    '''
async def get_items_from_project(organization: str, number: int, auth_scheme: AuthenticationScheme, force_new: bool = False, *, status: str | None = None, type_: str | None = None, page: int | None = None, per_page: int | None = None, cache_service: CacheService, created_at_from: str | None = None, created_at_to: str | None = None, updated_at_from: str | None = None, updated_at_to: str | None = None, summarize: bool | None = False, callback_urls: list[str] | None = None, waiting: bool | None = None) -> tuple[list[ProjectItem] | ProjectSummary, dict[str, Any]] | None:
    """Get items from a GitHub Project V2.

    Args:
        organization (str): Organization name
        number (int): Project number
        auth_scheme (AuthenticationScheme): Authentication Scheme
        force_new (bool, optional): If True, bypass cache and fetch new data
        status (str | None, optional): Optional status to filter items by
        type_ (str | None, optional): Optional type to filter items by
        page (int | None, optional): Page number (1-based)
        per_page (int | None, optional): Number of items per page
        cache_service (CacheService): Cache service
        created_at_from (str | None, optional): Optional start date to filter items by
        created_at_to (str | None, optional): Optional end date to filter items by
        updated_at_from (str | None, optional): Optional start date to filter items by
        updated_at_to (str | None, optional): Optional end date to filter items by
        custom_fields_filter (List[CustomFieldFilter] | None, optional): Optional list of custom field filters
        summarize (bool | None, optional): If True, only output the summary of the project
        callback_urls (List[str] | None, optional): Optional list of callback URLs
        waiting (bool | None, optional): If True, wait for completion. If False/None, run in background.

    Returns:
        tuple[list[ProjectItem] | ProjectSummary, dict[str, Any]] | None: List of project
            items or project summary if summarize is True with metadata; or
            None if background task is in progress
    """
async def get_projects_list(auth_scheme: AuthenticationScheme, organization: str, cache_service: CacheService | None = None, force_new: bool | None = False, *, query: str | None = None, order_by: OrderByField, direction: OrderByDirection, per_page: int | None = None, page: int | None = None) -> tuple[list[Project], ProjectListMeta]:
    """Get list of projects from a GitHub Organization.

    Args:
        auth_scheme: Authentication Scheme
        organization: Organization name
        query: Query to search for (Project name/string)
        order_by: Field to order by (created_at, number, title, updated_at)
        direction: Direction to order by (asc, desc)
        per_page: Number of items per page
        page: Page number (1-based)
        cache_service: Cache service for caching results
        force_new: If True, bypass cache and fetch new data
    Returns:
        A tuple containing:
        - List of Project objects
        - ProjectListMeta object with pagination info and metadata
    """
async def update_project_item(organization: str, project_number: int, item_id: int, fields: list[dict[str, int | str | float | None]], auth_scheme: AuthenticationScheme) -> dict:
    '''Update one or more field values for a GitHub Project V2 item.

    This function updates project item fields by making a single PATCH request
    to the GitHub API with all field updates in the request body.

    Args:
        organization (str): The organization name that owns the project.
        project_number (int): The project number.
        item_id (int): The unique identifier of the project item.
        fields (list[dict]): List of field updates. Each dict should contain:
            - "id" (int): The field ID (integer)
            - "value" (str | int | float | None): The new value
        auth_scheme (AuthenticationScheme): Authentication scheme with bearer token.

    Returns:
        dict: The updated project item data from GitHub REST API.

    Raises:
        HTTPError: If GitHub API request fails (404 for not found, 403 for
            forbidden, 422 for validation errors).
    '''
async def list_project_fields(organization: str, project_number: int, auth_scheme: AuthenticationScheme, cache_service: CacheService | None = None, per_page: int = 30, before: str | None = None, after: str | None = None, force_new: bool = False) -> tuple[list[dict], ProjectListMeta]:
    """List all fields for a specific organization-owned project.

    This function retrieves all custom fields configured for a GitHub Project V2,
    including field metadata such as field ID, name, data type, options (for
    single_select fields), and configuration (for iteration fields).

    Args:
        organization: The organization name.
        project_number: The project's number.
        auth_scheme: Authentication scheme for GitHub API.
        cache_service: Optional cache service for caching results.
        per_page: Number of results per page, max 100 (default: 30).
        before: A cursor from Link header. If specified, searches for results
            before this cursor.
        after: A cursor from Link header. If specified, searches for results
            after this cursor.
        force_new: If True, bypass cache and fetch fresh data.

    Returns:
        Tuple of (list of field dictionaries, pagination metadata).

    Raises:
        HTTPError: If the GitHub API returns an error.
        Exception: For other unexpected errors.
    """
