from bosa_core.cache import CacheService as CacheService
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.github.entities.project import Project as Project, ProjectItem as ProjectItem, ProjectListMeta as ProjectListMeta
from bosa_server_plugins.github.helper.projects import ProjectSummary as ProjectSummary, add_item_to_project as add_item_to_project, get_items_from_project as get_items_from_project, get_projects_list as get_projects_list
from bosa_server_plugins.github.requests.projects import GithubAddProjectItemRequest as GithubAddProjectItemRequest, GithubGetProjectItemRequest as GithubGetProjectItemRequest, GithubListProjectCardsRequest as GithubListProjectCardsRequest, GithubListProjectFieldsRequest as GithubListProjectFieldsRequest, GithubListProjectsRequest as GithubListProjectsRequest, GithubUpdateProjectItemRequest as GithubUpdateProjectItemRequest, OrderByDirection as OrderByDirection, OrderByField as OrderByField
from bosa_server_plugins.handler import ExposedDefaultHeaders as ExposedDefaultHeaders, Router as Router
from bosa_server_plugins.handler.decorators import exclude_from_mcp as exclude_from_mcp
from typing import Callable

class GithubProjectsRoutes:
    """Github Project Routes."""
    def __init__(self, router: Router, get_auth_scheme: Callable[[ExposedDefaultHeaders], AuthenticationScheme], cache: CacheService) -> None:
        """Initialize the GithubProjectsRoutes.

        Args:
            router (Router): The router object.
            get_auth_scheme (Callable[[ExposedDefaultHeaders], AuthenticationScheme]): The function to get
                the authentication scheme.
            cache (CacheService): The cache service.
        """
