from bosa_server_plugins.common.mimetypes import MimeTypes as MimeTypes
from bosa_server_plugins.google_drive.services.markdown_converters.converters.base import MarkdownConverter as MarkdownConverter
from bosa_server_plugins.google_drive.services.markdown_converters.converters.markitdown.helper import convert_to_markdown as convert_to_markdown

class PptConverter(MarkdownConverter, mime_type=MimeTypes.PPTX.value):
    """Converts PPT files to markdown format using markitdown library."""
    def convert(self, file_content: bytes) -> str:
        """Convert PPT content to markdown.

        Args:
            file_content (bytes): Raw PPT file content.

        Returns:
            str: Markdown representation of PPT content.

        Raises:
            ValueError: If conversion fails.
        """
