from datetime import datetime
from pydantic import BaseModel
from typing import ClassVar, Generic, Literal, TypeVar

T = TypeVar('T')
PROJECT_FRAGMENT: str
PROJECT_ITEM_FRAGMENT: str
CONTENTLESS_PROJECT_ITEM_FRAGMENT: str

class GQLProjectBasic(BaseModel):
    """Basic project model."""
    id: str
    number: int
    title: str
    url: str
    @classmethod
    def from_dict(cls, data: dict) -> GQLProjectBasic:
        """Create a GQLProjectBasic from a dictionary.

        Args:
            data: The dictionary to create the project from.

        Returns:
            GQLProjectBasic: The created project.
        """

class GQLProjectItemFieldValue(BaseModel, Generic[T]):
    """Project item field value model."""
    name: str
    value: T | None
    field_type: Literal['single_select', 'text', 'date', 'number']

class GQLProjectItemFieldSingleSelectValue(GQLProjectItemFieldValue[str]):
    """Single select field value."""
    FIELD_TYPE: ClassVar[Literal['single_select']]
    field_type: Literal['single_select']
    option_id: str

class GQLProjectItemFieldTextValue(GQLProjectItemFieldValue[str]):
    """Text field value."""
    FIELD_TYPE: ClassVar[Literal['text']]
    field_type: Literal['text']

class GQLProjectItemFieldDateValue(GQLProjectItemFieldValue[datetime]):
    """Date field value."""
    FIELD_TYPE: ClassVar[Literal['date']]
    field_type: Literal['date']

class GQLProjectItemFieldNumberValue(GQLProjectItemFieldValue[float]):
    """Number field value."""
    FIELD_TYPE: ClassVar[Literal['number']]
    field_type: Literal['number']

class GQLProjectItemBasic(BaseModel):
    """Basic project item model."""
    id: str
    type: str
    created_at: datetime
    updated_at: datetime
    field_values: list[GQLProjectItemFieldSingleSelectValue | GQLProjectItemFieldTextValue | GQLProjectItemFieldDateValue | GQLProjectItemFieldNumberValue]
    @classmethod
    def from_dict(cls, data: dict) -> GQLProjectItemBasic:
        """Create a GQLProjectItemBasic from a dictionary.

        Args:
            data: The dictionary to create the project item from.

        Returns:
            GQLProjectItemBasic: The created project item.
        """
