"""
Prefetch utilities for bulk loading connections and concepts.
"""

from typing import List, Set
from ccs.models.connection import Connection, create_default_connection
from ccs.data.local_connection_data import LocalConnectionData


async def get_connection_data_prefetch(connection_ids: List[int]) -> List[Connection]:
    """
    Prefetch connections and their related concepts for optimal performance.

    This function:
    1. Checks local cache for existing connections
    2. Fetches uncached connections from API in bulk
    3. Prefetches all related concepts (ofTheConcept, toConcept, type)

    Args:
        connection_ids: List of connection IDs to fetch

    Returns:
        List of Connection objects

    Example:
        >>> connection_ids = [1, 2, 3, 4, 5]
        >>> connections = await get_connection_data_prefetch(connection_ids)
        >>> for conn in connections:
        ...     print(f"{conn.ofTheConceptId} -> {conn.toTheConceptId}")
    """
    from ccs.api.get_connection import get_connection_bulk
    from ccs.api.get_concept import GetConceptBulk
    from ccs.services.get.get_the_concept import GetTheConcept

    connections_all: List[Connection] = []
    remaining_connection_ids: List[int] = []

    # Check local cache first
    for conn_id in connection_ids:
        connection = LocalConnectionData.GetConnection(conn_id)
        if connection and connection.id != 0:
            connections_all.append(connection)
        else:
            remaining_connection_ids.append(conn_id)

    # Fetch uncached connections from API
    if remaining_connection_ids:
        try:
            fetched_connections = await get_connection_bulk(remaining_connection_ids)
            connections_all.extend(fetched_connections)
        except Exception as e:
            print(f"Error fetching connections in bulk: {e}")

    # Collect all concept IDs to prefetch
    concept_ids_to_prefetch: Set[int] = set()
    for conn in connections_all:
        if conn.ofTheConceptId > 0:
            concept_ids_to_prefetch.add(conn.ofTheConceptId)
        if conn.toTheConceptId > 0:
            concept_ids_to_prefetch.add(conn.toTheConceptId)
        if conn.typeId > 0:
            concept_ids_to_prefetch.add(conn.typeId)

    # Prefetch all related concepts
    if concept_ids_to_prefetch:
        try:
            await GetConceptBulk(list(concept_ids_to_prefetch))
        except Exception as e:
            print(f"Error prefetching concepts: {e}")

    return connections_all


async def get_connections_with_concepts(connection_ids: List[int]) -> List[Connection]:
    """
    Get connections with their related concepts fully loaded.

    This is a convenience wrapper that prefetches and then loads
    the actual concept objects onto the connections.

    Args:
        connection_ids: List of connection IDs to fetch

    Returns:
        List of Connection objects with ofConcept, toConcept, and type populated
    """
    from ccs.services.get.get_the_concept import GetTheConcept

    connections = await get_connection_data_prefetch(connection_ids)

    # Load concepts onto connections
    for conn in connections:
        if conn.ofTheConceptId > 0 and conn.ofConcept is None:
            conn.ofConcept = await GetTheConcept(conn.ofTheConceptId)
        if conn.toTheConceptId > 0 and conn.toConcept is None:
            conn.toConcept = await GetTheConcept(conn.toTheConceptId)
        if conn.typeId > 0 and conn.type is None:
            conn.type = await GetTheConcept(conn.typeId)

    return connections
