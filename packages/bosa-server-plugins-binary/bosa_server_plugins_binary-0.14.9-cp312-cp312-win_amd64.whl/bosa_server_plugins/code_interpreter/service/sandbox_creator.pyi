from bosa_core import ConfigService as ConfigService
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.code_interpreter.constant import DEFAULT_LANGUAGE as DEFAULT_LANGUAGE, E2B_DOMAIN_ENV as E2B_DOMAIN_ENV, E2B_TEMPLATE_PYTHON_ENV as E2B_TEMPLATE_PYTHON_ENV
from bosa_server_plugins.code_interpreter.helper.file_watcher import E2BFileWatcher as E2BFileWatcher
from gllm_tools.code_interpreter.code_sandbox.e2b_sandbox import E2BSandbox

class SandboxCreatorService:
    """Sandbox creator for Code Interpreter Plugin.

    Attributes:
        auth_scheme (AuthenticationScheme): The authentication scheme to use.
        config_service (ConfigService): The config service to use.
        e2b_domain (str | None): The E2B domain to use.
        DEFAULT_ADDITIONAL_PACKAGES (list[str]): Default additional packages to install.
    """
    auth_scheme: AuthenticationScheme
    config_service: ConfigService
    template_id: str | None
    e2b_domain: str | None
    def __init__(self, auth_scheme: AuthenticationScheme, config_service: ConfigService) -> None:
        """Initialize the sandbox creator service.

        Args:
            auth_scheme (AuthenticationScheme): The authentication scheme to use.
            config_service (ConfigService): The config service to use.
        """
    async def create_sandbox(self, language: str = ..., additional_packages: list[str] | None = None) -> tuple[E2BSandbox, E2BFileWatcher]:
        '''Create and initialize the E2B Remote Sandbox.

        Args:
            language (str, optional): Programming language for the sandbox. Defaults to "python".
            additional_packages (list[str] | None, optional): Additional packages to install. Defaults to None.

        Returns:
            tuple[E2BSandbox, E2BFileWatcher]: Initialized sandbox instance and file watcher
        '''
