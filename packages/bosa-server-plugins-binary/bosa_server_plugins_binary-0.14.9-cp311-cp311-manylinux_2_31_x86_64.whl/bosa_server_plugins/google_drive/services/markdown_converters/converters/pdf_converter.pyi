from bosa_server_plugins.common.mimetypes import MimeTypes as MimeTypes
from bosa_server_plugins.google_drive.services.markdown_converters.converters.base import MarkdownConverter as MarkdownConverter
from bosa_server_plugins.google_drive.services.markdown_converters.converters.markitdown.helper import convert_to_markdown as convert_to_markdown

class PdfConverter(MarkdownConverter, mime_type=MimeTypes.PDF.value):
    """Converts PDF files to markdown format using markitdown library."""
    def convert(self, file_content: bytes) -> str:
        """Convert PDF content to markdown.

        Args:
            file_content (bytes): Raw PDF file content.

        Returns:
            str: Markdown representation of PDF content.

        Raises:
            ValueError: If conversion fails.
        """
