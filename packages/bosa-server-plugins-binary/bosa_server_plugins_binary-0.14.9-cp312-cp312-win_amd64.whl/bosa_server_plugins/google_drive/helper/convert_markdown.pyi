from bosa_server_plugins.google_drive.constants.convert_markdown import GOOGLE_DRIVE_CONVERT_MARKDOWN_DOWNLOAD_TIMEOUT_IN_SECONDS as GOOGLE_DRIVE_CONVERT_MARKDOWN_DOWNLOAD_TIMEOUT_IN_SECONDS
from bosa_server_plugins.google_drive.services.download import GoogleDriveDownloadService as GoogleDriveDownloadService
from bosa_server_plugins.google_drive.services.files import GoogleDriveFileService as GoogleDriveFileService
from bosa_server_plugins.google_drive.services.markdown_converters.markdown_converter import MarkdownConverterService as MarkdownConverterService

async def get_markdown_content(file_service: GoogleDriveFileService, download_service: GoogleDriveDownloadService, convert_service: MarkdownConverterService, *, file_id: str) -> dict[str, str]:
    """Convert a Google Drive file to markdown format.

    Args:
        file_service (GoogleDriveFileService): Service for file metadata operations.
        download_service (GoogleDriveDownloadService): Service for file download operations.
        convert_service (MarkdownConverterService): Service for file conversion operations.
        file_id (str): ID of the file to convert.

    Returns:
        dict: Dictionary containing filename and markdown content.

    Raises:
        NotFoundException: If file is not found on Google Drive.
        ValueError: If file format is not supported or conversion fails.
    """
