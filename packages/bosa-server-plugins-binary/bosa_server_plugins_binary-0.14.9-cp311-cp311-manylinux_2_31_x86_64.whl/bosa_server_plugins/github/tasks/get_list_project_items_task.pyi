from _typeshed import Incomplete
from bosa_core.cache import CacheService as CacheService
from bosa_server_plugins.auth.bearer import BearerTokenAuthentication as BearerTokenAuthentication
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.common.cache import deserialize_cache_data as deserialize_cache_data
from bosa_server_plugins.common.callback import with_callbacks as with_callbacks
from bosa_server_plugins.github.constant import GITHUB_PROJECTS_DEFAULT_TTL_IN_SECONDS as GITHUB_PROJECTS_DEFAULT_TTL_IN_SECONDS
from bosa_server_plugins.github.entities.project import ProjectItem as ProjectItem
from bosa_server_plugins.github.gql.project import PROJECT_ITEM_FRAGMENT as PROJECT_ITEM_FRAGMENT
from bosa_server_plugins.github.helper.connect import query_github_gql as query_github_gql
from pydantic import BaseModel
from typing import Any

PROJECT_ITEMS_QUERY: Incomplete

class GetItemsFromProjectParameter(BaseModel):
    """Get items from project parameter."""
    status: str | None
    type_: str | None
    created_at_from: str | None
    created_at_to: str | None
    updated_at_from: str | None
    updated_at_to: str | None
    summarize: bool
    callback_urls: list[str] | None

class ProjectSummaryField(BaseModel):
    """Project summary field."""
    field_name: str
    summaries: dict[str, Any]

class ProjectSummary(BaseModel):
    """Project summary."""
    total_items: int
    summary_fields: list[ProjectSummaryField]

def get_items_from_project_task(self, organization: str, number: int, auth_schema_key: str, item_key: str, parameter: dict, page: int, per_page: int):
    """Get items from a GitHub Project V2 and process with parameters.

    Args:
        self: Celery task instance
        organization: Organization name
        number: Project number
        auth_schema_key: Authentication scheme key
        item_key: Item cache key
        parameter: Get items from project parameter
        page: Page number
        per_page: Number of items per page

    Returns:
        Dictionary with fetched count and status
    """
def get_items_from_project_process(organization: str, number: int, auth_scheme: AuthenticationScheme, cache_service: CacheService, key: str) -> list[ProjectItem]:
    """Internal function to get items from a GitHub Project V2 with caching.

    Args:
        organization: Organization name
        number: Project number
        auth_scheme: Authentication Scheme
        cache_service: Cache service
        key: Cache key

    Returns:
        List of project items
    """
def process_items_from_project_request(items: list[ProjectItem], parameter: GetItemsFromProjectParameter, page: int, per_page: int) -> tuple[list[ProjectItem] | ProjectSummary, dict[str, Any]]:
    """Process filter items from project request.

    Args:
        items: List of project items
        parameter: Get items from project parameter
        page: Page number
        per_page: Number of items per page

    Returns:
        Tuple of list of project items or project summary and pagination metadata
    """
