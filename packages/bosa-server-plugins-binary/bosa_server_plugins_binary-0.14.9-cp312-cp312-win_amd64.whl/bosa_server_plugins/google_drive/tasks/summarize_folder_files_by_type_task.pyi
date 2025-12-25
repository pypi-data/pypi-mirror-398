from _typeshed import Incomplete
from bosa_core.cache import CacheService as CacheService
from bosa_server_plugins.common.cache import deserialize_cache_data as deserialize_cache_data, serialize_cache_data as serialize_cache_data
from bosa_server_plugins.common.callback import with_callbacks as with_callbacks
from bosa_server_plugins.google.auth.auth import GoogleCredentials as GoogleCredentials
from bosa_server_plugins.google_drive.constant import GOOGLE_AUTH_CACHE_KEY_FORMAT as GOOGLE_AUTH_CACHE_KEY_FORMAT
from bosa_server_plugins.google_drive.constants.summarize_folder_files import GOOGLE_DRIVE_SUMMARIZE_FOLDER_CACHE_RETRY_DELAY_SECONDS as GOOGLE_DRIVE_SUMMARIZE_FOLDER_CACHE_RETRY_DELAY_SECONDS, GOOGLE_DRIVE_SUMMARIZE_FOLDER_TASK_MAX_RETRY as GOOGLE_DRIVE_SUMMARIZE_FOLDER_TASK_MAX_RETRY, GOOGLE_DRIVE_SUMMARIZE_FOLDER_TOTAL_FILES_CACHE_TTL as GOOGLE_DRIVE_SUMMARIZE_FOLDER_TOTAL_FILES_CACHE_TTL
from bosa_server_plugins.google_drive.services.files import GoogleDriveFileService as GoogleDriveFileService
from bosa_server_plugins.google_drive.utils.file_type_mapping import get_file_type_category as get_file_type_category
from bosa_server_plugins.google_drive.utils.summarize_files import get_summarize_files_cache_key as get_summarize_files_cache_key

logger: Incomplete

def return_folder_summary(summary: dict, folder_id: str, callback_urls: list[str] | None) -> tuple[dict, list[str]]:
    """Prepare folder summary response with callback URLs.

    Args:
        summary (dict): The folder summary data
        folder_id (str): The ID of the folder
        callback_urls (list[str] | None): list of callback URLs

    Returns:
        tuple[dict, list[str]]: A tuple of (response_dict, callback_urls_list)
    """
def summarize_folder_files_by_type_task(folder_id: str, email: str, callback_urls: list[str] | None = None) -> tuple[dict, list[str]]:
    """Summarize all Google Drive files by type in a specific folder including files inside subfolders.

    Not include Google Drive folder.

    Args:
        folder_id (str): The ID of the folder to summarize
        email (str): The email of the user
        callback_urls (list[str] | None, optional): list of callback URLs to notify upon completion

    Returns:
        tuple[dict, list[str]]: A tuple of (response_dict, callback_urls_list) for @with_callbacks decorator
    """
