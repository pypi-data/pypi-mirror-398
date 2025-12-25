from _typeshed import Incomplete
from bosa_server_plugins.google.auth.auth import GoogleCredentials as GoogleCredentials
from bosa_server_plugins.google_drive.constants.convert_markdown import GOOGLE_DRIVE_CONVERT_MARKDOWN_DOWNLOAD_TIMEOUT_IN_SECONDS as GOOGLE_DRIVE_CONVERT_MARKDOWN_DOWNLOAD_TIMEOUT_IN_SECONDS
from bosa_server_plugins.google_drive.services.base import GoogleDriveServiceBase as GoogleDriveServiceBase
from typing import Any

class GoogleDriveDownloadService(GoogleDriveServiceBase):
    """Service class for Google Drive download operations.

    This class provides methods for downloading content from Google Drive
    using various endpoints of the Google Drive API.
    """
    credentials: Incomplete
    files_service: Incomplete
    revisions_service: Incomplete
    def __init__(self, credentials: GoogleCredentials) -> None:
        """Initialize the Google service with credentials.

        Args:
            credentials (GoogleCredentials): The credentials for the service
        """
    def export_file(self, params: dict[str, Any]) -> bytes:
        """Export a Google Workspace document.

        Args:
            params: Parameters for the files().export() request

        Returns:
            The exported file content
        """
    def get_revision_media(self, params: dict[str, Any]) -> bytes:
        """Get revision media content.

        Args:
            params: Parameters for the revisions().get_media() request

        Returns:
            The revision's media content
        """
    def get_file_media(self, params: dict[str, Any]) -> bytes:
        """Get file media content.

        Args:
            params: Parameters for the files().get_media() request

        Returns:
            The file's media content
        """
    async def download_file(self, file_id: str) -> tuple[bytes, str | None]:
        """Download a file using the unified files().download() API.

        This provides a simpler alternative to get_file_media()/export_file()
        for cases where the Drive API supports ``files().download``.

        Args:
            file_id (str): The ID of the file to download.

        Returns:
            tuple[bytes, str | None]: The downloaded file content and its mime type.
        """
