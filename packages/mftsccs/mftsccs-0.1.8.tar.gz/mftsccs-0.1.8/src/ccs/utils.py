"""
Utility functions for the CCS library.

This module contains helper functions and utilities that support
the main functionality of the library.
"""

from typing import List, Any, Optional


def helper_function(items: List[Any], default: Optional[Any] = None) -> Any:
    """
    A helper function that returns the first item or a default value.

    Args:
        items: A list of items to check.
        default: The default value to return if the list is empty.

    Returns:
        The first item in the list, or the default value if empty.

    Example:
        >>> from ccs.utils import helper_function
        >>> helper_function([1, 2, 3])
        1
        >>> helper_function([], "empty")
        'empty'
    """
    return items[0] if items else default


def validate_input(value: Any, expected_type: type) -> bool:
    """
    Validate that a value is of the expected type.

    Args:
        value: The value to validate.
        expected_type: The expected type of the value.

    Returns:
        True if the value is of the expected type, False otherwise.
    """
    return isinstance(value, expected_type)


def flatten_list(nested_list: List[List[Any]]) -> List[Any]:
    """
    Flatten a nested list into a single list.

    Args:
        nested_list: A list containing nested lists.

    Returns:
        A flattened list with all elements.

    Example:
        >>> flatten_list([[1, 2], [3, 4], [5]])
        [1, 2, 3, 4, 5]
    """
    return [item for sublist in nested_list for item in sublist]
