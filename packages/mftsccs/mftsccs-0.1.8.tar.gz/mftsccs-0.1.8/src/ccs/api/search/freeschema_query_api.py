"""
FreeschemaQueryApi - Executes FreeSchema queries against the CCS backend.
"""

import json
from typing import Any, Dict, List

from ccs.config.base_url import BaseUrl
from ccs.api.http_client import post_with_retry
from ccs.models.search.freeschema_query import FreeschemaQuery


async def freeschema_query_api(
    query: FreeschemaQuery,
    token: str = ""
) -> List[Any]:
    """
    Execute a FreeSchema query against the CCS backend.

    This function sends a FreeschemaQuery to the backend API and returns
    the matching results. It handles authentication, serialization, and
    error handling automatically.

    Args:
        query: The FreeschemaQuery object containing query parameters
        token: Optional authentication token (uses stored token if not provided)

    Returns:
        List of results from the query. Returns empty list on error.

    Example:
        >>> query = FreeschemaQuery(
        ...     type="the_person",
        ...     inpage=20,
        ...     page=1,
        ...     order="ASC"
        ... )
        >>> results = await freeschema_query_api(query)
        >>> for item in results:
        ...     print(item)

    Example with filters:
        >>> query = FreeschemaQuery(
        ...     type="the_document",
        ...     filters=[
        ...         FilterSearch(type="characterValue", search="%report%", logicoperator="LIKE")
        ...     ],
        ...     filterLogic="AND"
        ... )
        >>> results = await freeschema_query_api(query)
    """
    url = BaseUrl.FreeschemaQueryUrl()
    headers = {"Content-Type": "application/json"}

    # Convert query to JSON
    body = json.dumps(query.to_dict())

    try:
        response = await post_with_retry(url, headers=headers, data=body)

        if response.status == 200:
            result = await response.json()
            return result
        else:
            print(f"FreeschemaQueryApi error: HTTP {response.status}")
            return []

    except Exception as ex:
        print(f"FreeschemaQueryApi exception: {ex}")
        return []


async def freeschema_query_raw(
    query_dict: Dict[str, Any],
    token: str = ""
) -> List[Any]:
    """
    Execute a raw FreeSchema query using a dictionary.

    This is a lower-level function that accepts a raw dictionary
    instead of a FreeschemaQuery object. Useful for dynamic query
    construction or when working with query templates.

    Args:
        query_dict: Dictionary containing query parameters
        token: Optional authentication token

    Returns:
        List of results from the query. Returns empty list on error.

    Example:
        >>> query_dict = {
        ...     "type": "the_person",
        ...     "inpage": 10,
        ...     "page": 1,
        ...     "order": "DESC",
        ...     "filters": [],
        ...     "freeschemaQueries": []
        ... }
        >>> results = await freeschema_query_raw(query_dict)
    """
    url = BaseUrl.FreeschemaQueryUrl()
    headers = {"Content-Type": "application/json"}

    body = json.dumps(query_dict)

    try:
        response = await post_with_retry(url, headers=headers, data=body)

        if response.status == 200:
            result = await response.json()
            return result
        else:
            print(f"freeschema_query_raw error: HTTP {response.status}")
            return []

    except Exception as ex:
        print(f"freeschema_query_raw exception: {ex}")
        return []
