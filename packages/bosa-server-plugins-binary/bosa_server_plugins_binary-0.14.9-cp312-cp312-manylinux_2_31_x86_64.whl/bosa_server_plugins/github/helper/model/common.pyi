from enum import Enum, StrEnum

class Direction(StrEnum):
    """Direction for ordering results in REST API."""
    ASC = 'asc'
    DESC = 'desc'

class IssueCommentOrderField(str, Enum):
    """Issue comment order field model."""
    CREATED_AT = 'created_at'
    UPDATED_AT = 'updated_at'
