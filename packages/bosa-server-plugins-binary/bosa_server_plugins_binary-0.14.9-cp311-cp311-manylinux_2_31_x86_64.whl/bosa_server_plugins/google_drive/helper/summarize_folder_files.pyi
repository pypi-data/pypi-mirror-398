from _typeshed import Incomplete
from bosa_core.cache.interface import CacheService as CacheService
from bosa_server_plugins.background_task.utils import is_worker_available as is_worker_available
from bosa_server_plugins.common.cache import deserialize_cache_data as deserialize_cache_data
from bosa_server_plugins.common.callback import with_callbacks as with_callbacks
from bosa_server_plugins.google.auth.auth import GoogleCredentials as GoogleCredentials
from bosa_server_plugins.google.services.user_info import GoogleUserInfoService as GoogleUserInfoService
from bosa_server_plugins.google_drive.constant import GOOGLE_AUTH_CACHE_KEY_FORMAT as GOOGLE_AUTH_CACHE_KEY_FORMAT, GOOGLE_AUTH_CACHE_TTL as GOOGLE_AUTH_CACHE_TTL
from bosa_server_plugins.google_drive.tasks.summarize_folder_files_by_type_task import summarize_folder_files_by_type_task as summarize_folder_files_by_type_task
from bosa_server_plugins.google_drive.utils.summarize_files import get_summarize_files_cache_key as get_summarize_files_cache_key

logger: Incomplete

async def summarize_folder_total_files_by_type(auth_scheme: GoogleCredentials, cache_service: CacheService = None, *, folder_id: str, callback_urls: list[str] | None = None, waiting: bool | None = None) -> dict:
    """Summarize total files by type in Google Drive.

    Not include Google Drive folder.

    Args:
        auth_scheme (GoogleCredentials): GoogleCredentials instance
        cache_service (CacheService): CacheService instance
        folder_id (str): The ID of the folder to summarize
        callback_urls (list[str] | None, optional): List of callback URLs to send the response to
        waiting (bool | None, optional): Whether to wait for the task to complete

    Returns:
        dict: A dictionary containing the total number of files in a specific folder including files inside subfolders.
    """
