import abc
from abc import ABC, abstractmethod
from typing import ClassVar

class MarkdownConverter(ABC, metaclass=abc.ABCMeta):
    '''Abstract base class for file-to-markdown conversion.

    Subclasses must specify a ``mime_type`` parameter and implement ``convert``.
    The ``mime_type`` parameter is required for all subclasses.

    Usage: ``class PdfConverter(MarkdownConverter, mime_type="application/pdf")``

    Attributes:
        mime_type (ClassVar[str]): MIME type this converter handles.
    '''
    mime_type: ClassVar[str]
    def __init_subclass__(cls, mime_type: str | None = None, **kwargs) -> None:
        """Validate that ``mime_type`` is provided by subclasses.

        Args:
            mime_type (str): MIME type this converter handles (required).
            **kwargs: Additional keyword arguments.

        Raises:
            TypeError: If ``mime_type`` is not provided.
        """
    @abstractmethod
    def convert(self, file_content: bytes) -> str:
        """Convert file content to markdown.

        Args:
            file_content (bytes): Raw file content.

        Returns:
            str: Markdown representation of file content.
        """
