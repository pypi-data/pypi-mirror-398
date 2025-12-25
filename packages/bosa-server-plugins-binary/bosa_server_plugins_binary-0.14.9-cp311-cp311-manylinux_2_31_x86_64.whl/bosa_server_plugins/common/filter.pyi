import abc
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel, RootModel
from typing import Any, Literal

def filter_items_by_custom_fields(items: list[dict[str, Any]] | dict[str, Any], custom_fields_filter: list['CustomFieldFilter'] | None = None) -> list[dict[str, Any]] | dict[str, Any]:
    '''Filter items by custom fields using direct object structure.

    Only filters if input is a list. Single dict inputs are returned as-is.
    Root filters can still modify arrays within dicts.

    Args:
        items: List of item dictionaries or a single item dictionary.
               Items are accessed directly using field names.
               Supports nested fields using dot notation (e.g., "creator.age").
               Regular filters only apply to list inputs. Single dict inputs are returned
               unchanged (except for root filter modifications to arrays within).
        custom_fields_filter: List of custom field filters to apply. If None or empty,
                             returns all items unfiltered. Defaults to None.
                             Filters with \'root\' set will filter arrays within items.

    Returns:
        Filtered list of item dictionaries if input was a list, or the original dict
        if input was a dict. Items with root filters have their arrays modified to contain
        only matching elements. If items is not a list or dict, returns items unchanged.

    Examples:
        >>> items = [
        ...     {"creator": "johndoe", "status": "open"},
        ...     {"creator": "john", "status": "closed"}
        ... ]
        >>> filter_obj = CustomFieldFilter.model_validate({
        ...     "type": "string",
        ...     "field_name": "creator",
        ...     "value": "johndoe"
        ... })
        >>> filtered = filter_items_by_custom_fields(items, [filter_obj])
        >>> len(filtered)
        1

        >>> # Single dict input (returned as-is, not filtered)
        >>> item = {"creator": "johndoe", "status": "open"}
        >>> filtered = filter_items_by_custom_fields(item, [filter_obj])
        >>> filtered == item
        True

        >>> # Root filter example - modifies arrays within dict
        >>> item = {
        ...     "payload": {
        ...         "headers": [
        ...             {"name": "Received", "value": "..."},
        ...             {"name": "X-Received", "value": "..."}
        ...         ]
        ...     }
        ... }
        >>> root_filter = CustomFieldFilter.model_validate({
        ...     "type": "string_list",
        ...     "root": "payload.headers",
        ...     "field_name": "name",
        ...     "values": ["Received"]
        ... })
        >>> filtered = filter_items_by_custom_fields(item, [root_filter])
        >>> filtered["payload"]["headers"]
        [{"name": "Received", "value": "..."}]
    '''

class FilterType(str, Enum):
    """Filter type enum for discriminated union."""
    DATE_RANGE = 'date_range'
    STRING = 'string'
    STRING_LIST = 'string_list'
    NUMBER = 'number'
    NUMBER_LIST = 'number_list'
    NUMBER_RANGE = 'number_range'

class BaseCustomFieldFilter(BaseModel, ABC, metaclass=abc.ABCMeta):
    '''Base class for all custom field filters.

    Filters work with direct object structure, accessing fields by name.
    Supports nested fields using dot notation (e.g., "creator.age").

    Note:
        Field names are case-sensitive for optimal performance.
        Use exact field names as they appear in the data.
    '''
    field_name: str
    root: str | None
    @abstractmethod
    def apply(self, item: dict[str, Any]) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item dictionary to apply the filter to.
                  Fields are accessed directly using the field_name.
                  Supports nested fields with dot notation.

        Returns:
            True if the item passes the filter, False otherwise.
        """

class DateRangeFilter(BaseCustomFieldFilter):
    """Filter items by a date range.

    Args:
        from_date: Start date of the range
        to_date: End date of the range
    """
    type: Literal[FilterType.DATE_RANGE]
    from_date: str | None
    to_date: str | None
    def apply(self, item: dict[str, Any]) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item dictionary to apply the filter to.
        """

class StringFilter(BaseCustomFieldFilter):
    """Filter items by string value."""
    type: Literal[FilterType.STRING]
    value: str
    ignore_case: bool | None
    def apply(self, item: dict[str, Any]) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item dictionary to apply the filter to.
        """

class StringListFilter(BaseCustomFieldFilter):
    """Filter items by a list of string values."""
    type: Literal[FilterType.STRING_LIST]
    values: list[str]
    ignore_case: bool | None
    def apply(self, item: dict[str, Any]) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item dictionary to apply the filter to.
        """

class NumberFilter(BaseCustomFieldFilter):
    """Filter items by a number.

    Args:
        value: Value to filter by
    """
    type: Literal[FilterType.NUMBER]
    value: float
    def apply(self, item: dict[str, Any]) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item dictionary to apply the filter to.
        """

class NumberListFilter(BaseCustomFieldFilter):
    """Filter items by a list of numbers.

    Args:
        values: List of values to filter by
    """
    type: Literal[FilterType.NUMBER_LIST]
    values: list[float]
    def apply(self, item: dict[str, Any]) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item dictionary to apply the filter to.
        """

class NumberRangeFilter(BaseCustomFieldFilter):
    """Filter items by a number range. If none of the value is provided, will always return True.

    Args:
        from_value: Start value of the range. If not provided, will ignore the lower bound.
        to_value: End value of the range. If not provided, will ignore the upper bound.
    """
    type: Literal[FilterType.NUMBER_RANGE]
    from_value: float | None
    to_value: float | None
    def apply(self, item: dict[str, Any]) -> bool:
        """Apply the filter to the item.

        Args:
            item: The item dictionary to apply the filter to.

        Returns:
            True if the item passes the filter, False otherwise.
            Will always return True if both from_value and to_value are not provided.
        """

FilterUnion: Incomplete

class CustomFieldFilter(RootModel[FilterUnion]):
    '''Root model for all filter types that uses discriminated union.

    This class uses the \'type\' field to determine which filter to instantiate.
    Example usage in a request:

    ```json
    {
      "filters": [
        {
          "type": "date_range",
          "field_name": "due_date",
          "from_date": "2023-01-01T00:00:00Z",
          "to_date": "2023-12-31T23:59:59Z"
        },
        {
          "type": "string_list",
          "field_name": "status",
          "values": ["open", "in progress"]
        }
      ]
    }
    ```
    '''
    def apply(self, item: dict[str, Any]) -> bool:
        """Apply the filter to the item dictionary."""
    @property
    def field_name(self) -> str:
        """Get the field name."""
    @property
    def root_path(self) -> str | None:
        """Get the root path for array filtering."""
