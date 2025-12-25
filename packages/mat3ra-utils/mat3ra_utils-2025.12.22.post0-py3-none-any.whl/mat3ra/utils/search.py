import re
from typing import List, Optional, TypeVar

T = TypeVar("T")


def find_by_key_or_regex(
    items: List[T],
    key: str,
    value: Optional[str] = None,
    value_regex: Optional[str] = None,
) -> Optional[T]:
    """
    Find an item in a list by exact key value match or regex pattern.

    Args:
        items: List of objects to search through
        key: Name of the attribute to search on
        value: Exact value to match (takes precedence if both value and value_regex provided)
        value_regex: Regex pattern to match against attribute values

    Returns:
        First matching item or None if no match found or no search criteria provided

    Raises:
        ValueError: If both value and value_regex are provided
    """
    if value is not None and value_regex is not None:
        raise ValueError("Cannot specify both 'value' and 'value_regex'. Please provide only one.")

    if value is not None:
        if not isinstance(value, str):
            value = str(value)
        value_lower = value.lower()
        for item in items:
            item_value = getattr(item, key, None)
            if item_value is not None and str(item_value).lower() == value_lower:
                return item
    elif value_regex is not None:
        if not isinstance(value_regex, str):
            value_regex = str(value_regex)
        pattern = re.compile(value_regex, re.IGNORECASE)
        for item in items:
            item_value = getattr(item, key, None)
            if item_value is not None and pattern.search(str(item_value)):
                return item
    return None

