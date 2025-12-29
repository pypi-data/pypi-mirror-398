"""
GetConnection API - Fetches connections from the backend.
"""

import json
from typing import List

from ccs.models.connection import Connection, create_default_connection
from ccs.config.base_url import BaseUrl
from ccs.data.local_connection_data import LocalConnectionData
from ccs.api.http_client import post_with_retry


async def get_connection(id: int) -> Connection:
    """
    Fetches a connection from the backend API by its ID.

    Args:
        id: The ID of the connection to fetch

    Returns:
        The Connection object if found, or a default empty Connection if not found.
    """
    result = create_default_connection()

    if id is None or id == 0:
        return result

    # Check local cache first
    cached = LocalConnectionData.GetConnection(id)
    if cached and cached.id != 0:
        return cached

    # Fetch from backend API
    try:
        url = BaseUrl.GetConnectionUrl()
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"id": str(id)}

        response = await post_with_retry(url, headers=headers, data=data)

        if response.status == 200:
            json_data = await response.json()
            result = _parse_connection(json_data)

            if result.id > 0:
                LocalConnectionData.AddConnection(result)

    except Exception as e:
        print(f"get_connection error: {e}")

    return result


async def get_connection_bulk(ids: List[int]) -> List[Connection]:
    """
    Fetches multiple connections from the backend API in a single request.

    Args:
        ids: List of connection IDs to fetch

    Returns:
        List of Connection objects

    Example:
        >>> connections = await get_connection_bulk([1, 2, 3, 4, 5])
        >>> for conn in connections:
        ...     print(f"{conn.ofTheConceptId} -> {conn.toTheConceptId}")
    """
    results: List[Connection] = []
    missing_ids: List[int] = []

    # Check cache first
    for conn_id in ids:
        if conn_id is None or conn_id == 0:
            continue
        cached = LocalConnectionData.GetConnection(conn_id)
        if cached and cached.id != 0:
            results.append(cached)
        else:
            missing_ids.append(conn_id)

    # Fetch missing from API
    if missing_ids:
        try:
            url = BaseUrl.GetConnectionBulkUrl()
            headers = {"Content-Type": "application/json"}
            body = json.dumps(missing_ids)

            response = await post_with_retry(url, headers=headers, data=body)

            if response.status == 200:
                json_data = await response.json()
                if isinstance(json_data, list):
                    for item in json_data:
                        connection = _parse_connection(item)
                        if connection.id > 0:
                            LocalConnectionData.AddConnection(connection)
                            results.append(connection)

        except Exception as e:
            print(f"get_connection_bulk error: {e}")

    return results


def _parse_connection(data: dict) -> Connection:
    """Parse a connection from JSON response data."""
    if not data or not isinstance(data, dict):
        return create_default_connection()

    try:
        connection = Connection(
            id=data.get("id", 0),
            ofTheConceptId=data.get("ofTheConceptId", 0),
            toTheConceptId=data.get("toTheConceptId", 0),
            userId=data.get("userId", 0),
            typeId=data.get("typeId", 0),
            orderId=data.get("orderId", 1),
            accessId=data.get("accessId", 4),
        )
        connection.typeCharacter = data.get("typeCharacter", "")
        connection.ghostId = data.get("ghostId", 0)

        # Handle timestamps
        if "entryTimeStamp" in data:
            from datetime import datetime
            try:
                connection.entryTimeStamp = datetime.fromisoformat(
                    data["entryTimeStamp"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        return connection

    except Exception as e:
        print(f"Error parsing connection: {e}")
        return create_default_connection()
