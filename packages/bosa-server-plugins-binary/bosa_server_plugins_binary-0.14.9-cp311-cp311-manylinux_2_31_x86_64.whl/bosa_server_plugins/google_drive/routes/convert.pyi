from bosa_server_plugins.google.auth.auth import GoogleCredentials as GoogleCredentials
from bosa_server_plugins.google_drive.helper import convert_markdown as convert_markdown
from bosa_server_plugins.google_drive.requests.download import ConvertMarkdownRequest as ConvertMarkdownRequest
from bosa_server_plugins.google_drive.services.download import GoogleDriveDownloadService as GoogleDriveDownloadService
from bosa_server_plugins.google_drive.services.files import GoogleDriveFileService as GoogleDriveFileService
from bosa_server_plugins.google_drive.services.markdown_converters.markdown_converter import MarkdownConverterService as MarkdownConverterService
from bosa_server_plugins.handler import ExposedDefaultHeaders as ExposedDefaultHeaders, Router as Router
from typing import Callable

class GoogleDriveConvertRoutes:
    """Routes exposing convert-to-markdown functionality."""
    def __init__(self, router: Router, get_auth_scheme: Callable[[ExposedDefaultHeaders], GoogleCredentials]) -> None:
        """Register convert-to-markdown endpoint.

        Args:
            router: Router instance to attach endpoints to.
            get_auth_scheme: Function that extracts GoogleCredentials from headers.
        """
