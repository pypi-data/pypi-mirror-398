GOOGLE_DRIVE_SUMMARIZE_ALL_FILES_CACHE_KEY: str
GOOGLE_DRIVE_SUMMARIZE_FOLDER_TOTAL_FILES_CACHE_KEY: str

def get_summarize_all_files_cache_key(email: str) -> str:
    """Get the cache key for summarizing all files by type.

    Args:
        email (str): The email of the user

    Returns:
        str: Cache key for summarizing all files
    """
def get_summarize_files_cache_key(email: str, folder_id: str) -> str:
    """Get the cache key for summarizing files by type.

    Args:
        email: The email of the user
        folder_id: The ID of the folder to summarize
    """
