"""
Flatten utilities for converting nested query results to simple dictionaries.

Handles multi-level nested JSON from freeschemaQueries, for example:
- Project → Tasks → Subtasks
- Person → Addresses → City
"""

from typing import Any, Dict, List


def flatten_query_result(data: List[Dict[str, Any]], max_depth: int = 10) -> List[Dict[str, Any]]:
    """
    Flatten nested query results into simple key-value dictionaries.

    Handles multi-level nesting from freeschemaQueries. Nested entities
    are flattened into arrays with their own flattened structure.

    Converts deeply nested structures like:
    {
        "id": 123,
        "data": {
            "the_project": {
                "the_project_name": {"id": 1, "data": {"the_name": "My Project"}},
                "the_project_s_task_s": [
                    {
                        "id": 456,
                        "data": {
                            "the_task": {
                                "the_task_name": {"id": 2, "data": {"the_name": "Task 1"}}
                            }
                        }
                    }
                ]
            }
        }
    }

    Into flat structures like:
    {
        "id": 123,
        "the_project_name": "My Project",
        "the_project_s_task_s": [
            {"id": 456, "the_task_name": "Task 1"}
        ]
    }

    Args:
        data: List of nested result dictionaries from schema_query_listener
        max_depth: Maximum recursion depth to prevent infinite loops

    Returns:
        List of flattened dictionaries with simple key-value pairs

    Example:
        >>> result = await schema_query_listener(query)
        >>> flat_data = flatten_query_result(result.data)
        >>> for item in flat_data:
        ...     print(f"Name: {item.get('the_name')}")
        ...     for task in item.get('the_project_s_task_s', []):
        ...         print(f"  Task: {task.get('the_task_name')}")
    """
    if not data:
        return []

    flattened_results: List[Dict[str, Any]] = []

    for item in data:
        flat_item = _flatten_item(item, max_depth)
        flattened_results.append(flat_item)

    return flattened_results


def _flatten_item(item: Dict[str, Any], max_depth: int = 10, current_depth: int = 0) -> Dict[str, Any]:
    """
    Flatten a single nested item into a simple dictionary.

    Args:
        item: Nested dictionary with id, data, and optional created_on
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth

    Returns:
        Flattened dictionary
    """
    if current_depth > max_depth:
        return item  # Return as-is to prevent infinite recursion

    flat: Dict[str, Any] = {}

    # Preserve top-level id
    if "id" in item:
        flat["id"] = item["id"]

    # Preserve created_on timestamp
    if "created_on" in item:
        flat["created_on"] = item["created_on"]

    # Preserve count if present
    if "count" in item:
        flat["count"] = item["count"]

    # Flatten the nested data structure
    if "data" in item and isinstance(item["data"], dict):
        _extract_values(item["data"], flat, max_depth, current_depth + 1)

    return flat


def _extract_values(
    data: Any,
    flat: Dict[str, Any],
    max_depth: int = 10,
    current_depth: int = 0
) -> None:
    """
    Recursively extract values from nested data structures.

    Args:
        data: The nested data to extract from
        flat: The flat dictionary to populate
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth
    """
    if current_depth > max_depth:
        return

    if not isinstance(data, dict):
        return

    for key, value in data.items():
        if isinstance(value, dict):
            # Check if this is a leaf node with "id" and "data"
            if "id" in value and "data" in value:
                # This is a nested composition/entity - flatten it recursively
                nested_flat = _flatten_item(value, max_depth, current_depth)

                # Check if it has meaningful nested data or just simple value
                if len(nested_flat) > 3:  # More than just id, created_on, count
                    # It's a nested entity - store as flattened object
                    flat[key] = nested_flat
                else:
                    # It's a simple value node - extract the actual value
                    inner_data = value["data"]
                    if isinstance(inner_data, dict):
                        for inner_key, inner_value in inner_data.items():
                            flat[key] = inner_value
                            flat[f"{key}_id"] = value["id"]
                            break  # Usually only one value
                    else:
                        flat[key] = inner_data
                        flat[f"{key}_id"] = value["id"]

            elif "id" in value and "data" not in value:
                # Just an ID reference
                flat[key] = value
            else:
                # Recurse into nested structure (type wrapper like "the_person")
                _extract_values(value, flat, max_depth, current_depth + 1)

        elif isinstance(value, list):
            # Handle arrays of nested items (from _s_ connections)
            flattened_list = []
            for v in value:
                if isinstance(v, dict):
                    if "id" in v and "data" in v:
                        # Nested entity - flatten it
                        flattened_list.append(_flatten_item(v, max_depth, current_depth + 1))
                    elif "id" in v:
                        # Simple reference
                        flattened_list.append(_flatten_item(v, max_depth, current_depth + 1))
                    else:
                        # Regular dict
                        flattened_list.append(v)
                else:
                    flattened_list.append(v)
            flat[key] = flattened_list

        else:
            # Simple value
            flat[key] = value


def flatten_to_simple(
    data: List[Dict[str, Any]],
    strip_prefix: bool = True,
    max_depth: int = 10
) -> List[Dict[str, Any]]:
    """
    Flatten query results to the simplest possible format.

    This removes "the_" prefixes and extracts just the essential values.
    Also handles multi-level nested structures.

    Args:
        data: List of nested result dictionaries
        strip_prefix: If True, removes "the_" prefix from keys
        max_depth: Maximum recursion depth for nested structures

    Returns:
        List of simple dictionaries

    Example:
        >>> result = await schema_query_listener(query)
        >>> simple = flatten_to_simple(result.data)
        >>> # Instead of item["the_llm_tracker_model"], use item["llm_tracker_model"]
        >>> # Nested: item["project_s_task_s"][0]["task_name"]
    """
    flattened = flatten_query_result(data, max_depth)

    if not strip_prefix:
        return flattened

    simple_results: List[Dict[str, Any]] = []

    for item in flattened:
        simple_item = _strip_prefixes(item)
        simple_results.append(simple_item)

    return simple_results


def _strip_prefixes(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively strip 'the_' prefixes from all keys in a dictionary.

    Args:
        item: Dictionary with keys to strip

    Returns:
        Dictionary with stripped keys
    """
    simple_item: Dict[str, Any] = {}

    for key, value in item.items():
        # Strip "the_" prefix
        new_key = key[4:] if key.startswith("the_") else key

        if isinstance(value, dict):
            # Recursively strip prefixes from nested dicts
            simple_item[new_key] = _strip_prefixes(value)
        elif isinstance(value, list):
            # Handle arrays - strip prefixes from nested items
            simple_item[new_key] = [
                _strip_prefixes(v) if isinstance(v, dict) else v
                for v in value
            ]
        else:
            simple_item[new_key] = value

    return simple_item


def flatten_to_records(
    data: List[Dict[str, Any]],
    include_nested: bool = False,
    separator: str = "."
) -> List[Dict[str, Any]]:
    """
    Flatten to completely flat records suitable for tabular data (CSV, DataFrame).

    Nested structures are either excluded or flattened with dot notation.

    Args:
        data: List of nested result dictionaries
        include_nested: If True, flatten nested arrays using dot notation
        separator: Separator for nested keys (default ".")

    Returns:
        List of completely flat dictionaries

    Example:
        >>> records = flatten_to_records(result.data)
        >>> # {"id": 123, "name": "John", "email": "john@example.com"}

        >>> records = flatten_to_records(result.data, include_nested=True)
        >>> # {"id": 123, "name": "John", "tasks.0.name": "Task 1", "tasks.1.name": "Task 2"}
    """
    flattened = flatten_to_simple(data)
    records: List[Dict[str, Any]] = []

    for item in flattened:
        record: Dict[str, Any] = {}
        _flatten_to_record(item, record, "", separator, include_nested)
        records.append(record)

    return records


def _flatten_to_record(
    item: Any,
    record: Dict[str, Any],
    prefix: str,
    separator: str,
    include_nested: bool
) -> None:
    """
    Recursively flatten an item to a completely flat record.

    Args:
        item: Item to flatten
        record: Record dictionary to populate
        prefix: Current key prefix
        separator: Separator for nested keys
        include_nested: Whether to include nested arrays
    """
    if isinstance(item, dict):
        for key, value in item.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key

            if isinstance(value, dict):
                _flatten_to_record(value, record, new_key, separator, include_nested)
            elif isinstance(value, list):
                if include_nested:
                    for i, v in enumerate(value):
                        _flatten_to_record(v, record, f"{new_key}{separator}{i}", separator, include_nested)
                # Skip lists if not including nested
            else:
                record[new_key] = value
    else:
        if prefix:
            record[prefix] = item
