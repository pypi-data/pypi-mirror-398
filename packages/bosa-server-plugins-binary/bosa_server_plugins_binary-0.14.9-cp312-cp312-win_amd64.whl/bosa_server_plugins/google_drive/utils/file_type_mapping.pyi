from _typeshed import Incomplete
from bosa_server_plugins.common.mimetypes import MimeTypes as MimeTypes

MIMETYPE_TO_FILE_TYPE: Incomplete

def get_file_type_category(mime_type: str) -> str:
    """Get the standardized file type category from a MIME type.

    Args:
        mime_type (str): The MIME type string

    Returns:
        str: A standardized file type category or 'others' if the MIME type is not recognized
    """
