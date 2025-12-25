from bosa_server_plugins.github.constant import DEFAULT_ITEM_PER_PAGE as DEFAULT_ITEM_PER_PAGE, DEFAULT_PAGE as DEFAULT_PAGE, MAXIMUM_ITEM_PER_PAGE as MAXIMUM_ITEM_PER_PAGE, MINIMUM_ITEM_PER_PAGE as MINIMUM_ITEM_PER_PAGE
from bosa_server_plugins.handler import BaseRequestModel as BaseRequestModel

class BasicRepositoryRequest(BaseRequestModel):
    """Request model for getting repository contributors."""
    owner: str
    repo: str

class GetContributorsRequest(BasicRepositoryRequest):
    """Request model for getting repository contributors."""
    anon: bool | None
    per_page: int | None
    page: int | None

class SearchContributorsRequest(BaseRequestModel):
    """Request model for searching repository contributors."""
    name: str
    repositories: list[str] | None
    since: str
    until: str
