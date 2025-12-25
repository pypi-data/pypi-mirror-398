from bosa_core import ConfigService as ConfigService
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.code_interpreter.requests.execute_code import ExecuteCodeRequest as ExecuteCodeRequest
from bosa_server_plugins.code_interpreter.service.sandbox_creator import SandboxCreatorService as SandboxCreatorService
from bosa_server_plugins.handler.header import ExposedDefaultHeaders as ExposedDefaultHeaders
from bosa_server_plugins.handler.router import Router as Router
from typing import Callable

class ExecuteCodeRoutes:
    """Code Interpreter execute code routes."""
    def __init__(self, router: Router, get_auth_scheme: Callable[[ExposedDefaultHeaders], AuthenticationScheme], config_service: ConfigService) -> None:
        """Initialize the Code Interpreter execute code routes.

        Args:
            router (Router): The router object.
            get_auth_scheme (Callable[[ExposedDefaultHeaders], AuthenticationScheme]): The function to get
                the authentication scheme.
            config_service (ConfigService): The config service to use.
        """
