from _typeshed import Incomplete
from bosa_server_plugins.code_interpreter.constant import FILE_WATCHER_POLL_INTERVAL_SECONDS as FILE_WATCHER_POLL_INTERVAL_SECONDS
from e2b_code_interpreter import Sandbox as Sandbox, WatchHandle as WatchHandle

class E2BFileWatcher:
    """File watcher for monitoring file creation in E2B sandbox environments.

    Attributes:
        sandbox (Sandbox): The sandbox instance to monitor.
    """
    sandbox: Incomplete
    def __init__(self, sandbox: Sandbox) -> None:
        """Initialize the file watcher with a sandbox instance.

        Args:
            sandbox (Sandbox): The sandbox instance to monitor.
        """
    async def setup_monitoring(self, output_dirs: list[str] | None = None) -> None:
        """Set up filesystem watchers for monitoring file creation.

        Args:
            output_dirs (list[str] | None, optional): List of output directories to monitor.
                Defaults to None, which is converted to an empty list.
        """
    async def process_events(self) -> None:
        """Process filesystem events from watchers and update created files list."""
    def reset_created_files(self) -> None:
        """Reset the list of created files."""
    def get_created_files(self) -> list[str]:
        """Get the list of files created during monitoring.

        Returns:
            List[str]: List of file paths that were created.
        """
