from _typeshed import Incomplete
from bosa_core.cache import CacheService as CacheService
from bosa_server_plugins.common.cache import serialize_cache_data as serialize_cache_data
from bosa_server_plugins.google.auth.auth import GoogleCredentials as GoogleCredentials
from bosa_server_plugins.google_drive.constant import GOOGLE_AUTH_CACHE_KEY_FORMAT as GOOGLE_AUTH_CACHE_KEY_FORMAT
from bosa_server_plugins.google_drive.constants.summarize_all_files import GOOGLE_DRIVE_SUMMARIZE_ALL_FILES_CACHE_RETRY_DELAY_SECONDS as GOOGLE_DRIVE_SUMMARIZE_ALL_FILES_CACHE_RETRY_DELAY_SECONDS, GOOGLE_DRIVE_SUMMARIZE_ALL_FILES_CACHE_TTL as GOOGLE_DRIVE_SUMMARIZE_ALL_FILES_CACHE_TTL, GOOGLE_DRIVE_SUMMARIZE_ALL_FILES_TASK_MAX_RETRY as GOOGLE_DRIVE_SUMMARIZE_ALL_FILES_TASK_MAX_RETRY
from bosa_server_plugins.google_drive.services.files import GoogleDriveFileService as GoogleDriveFileService
from bosa_server_plugins.google_drive.utils.file_type_mapping import get_file_type_category as get_file_type_category
from bosa_server_plugins.google_drive.utils.summarize_files import get_summarize_all_files_cache_key as get_summarize_all_files_cache_key

logger: Incomplete

def summarize_all_files_by_type_task(email: str) -> dict:
    """Summarize all Google Drive files by type accessible by the user.

    Not include Google Drive folder.

    Args:
        email (str): The email of the user

    Returns:
        dict: A dictionary containing the total number of files by type category
    """
