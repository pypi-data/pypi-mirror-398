from _typeshed import Incomplete
from bosa_core.cache.interface import CacheService as CacheService
from bosa_server_plugins.background_task.utils import is_worker_available as is_worker_available
from bosa_server_plugins.common.cache import deserialize_cache_data as deserialize_cache_data
from bosa_server_plugins.google.auth.auth import GoogleCredentials as GoogleCredentials
from bosa_server_plugins.google.services.user_info import GoogleUserInfoService as GoogleUserInfoService
from bosa_server_plugins.google_drive.constant import GOOGLE_AUTH_CACHE_KEY_FORMAT as GOOGLE_AUTH_CACHE_KEY_FORMAT, GOOGLE_AUTH_CACHE_TTL as GOOGLE_AUTH_CACHE_TTL
from bosa_server_plugins.google_drive.tasks.summarize_all_files_by_type_task import summarize_all_files_by_type_task as summarize_all_files_by_type_task
from bosa_server_plugins.google_drive.utils.summarize_files import get_summarize_all_files_cache_key as get_summarize_all_files_cache_key

logger: Incomplete

async def summarize_total_files_by_type(auth_scheme: GoogleCredentials, cache_service: CacheService = None, waiting: bool | None = None) -> dict:
    """Summarize total files by type in Google Drive.

    Not include Google Drive folder.

    Args:
        auth_scheme (GoogleCredentials): GoogleCredentials instance
        cache_service (CacheService): CacheService instance
        waiting (bool | None): Whether to wait for the task to complete

    Returns:
        dict: A dictionary containing the total number of files by type category in My Drive, Shared with Me,
            and combined.
    """
