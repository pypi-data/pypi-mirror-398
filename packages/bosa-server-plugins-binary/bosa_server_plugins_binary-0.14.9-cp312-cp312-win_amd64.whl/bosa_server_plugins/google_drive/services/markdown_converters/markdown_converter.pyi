from bosa_server_plugins.google_drive.services.markdown_converters.converters.base import MarkdownConverter as MarkdownConverter
from bosa_server_plugins.google_drive.services.markdown_converters.converters.docs_converter import DocxConverter as DocxConverter
from bosa_server_plugins.google_drive.services.markdown_converters.converters.pdf_converter import PdfConverter as PdfConverter
from bosa_server_plugins.google_drive.services.markdown_converters.converters.ppt_converter import PptConverter as PptConverter

class MarkdownConverterService:
    """Service to manage Markdown converters by MIME type.

    Instance-based service managing Markdown converters keyed by MIME type.
    """
    def __init__(self) -> None:
        """Initialize service and register built-in converters as instances."""
    def get_converter(self, mime_type: str) -> MarkdownConverter:
        """Get appropriate converter instance for MIME type.

        Args:
            mime_type (str): The MIME type to convert.

        Returns:
            MarkdownConverter: The converter instance for the given MIME type.

        Raises:
            ValueError: If no converter is registered for the MIME type.
        """
    def get_supported_mime_types(self) -> list[str]:
        """Get list of supported MIME types.

        Returns:
            list[str]: List of supported MIME types.
        """
