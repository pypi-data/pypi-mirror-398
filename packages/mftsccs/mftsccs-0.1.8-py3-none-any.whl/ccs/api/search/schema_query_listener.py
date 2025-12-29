"""
SchemaQueryListener - High-level wrapper for FreeSchema queries with result formatting.
"""

from typing import Any, Dict, List
from dataclasses import dataclass, field

from ccs.constants.format_constants import NORMAL, DATAID, JUSTDATA, ALLID, DATAV2
from ccs.models.search.freeschema_query import FreeschemaQuery
from ccs.api.search.freeschema_query_api import freeschema_query_api


@dataclass
class SchemaQueryResult:
    """
    Container for FreeSchema query results with metadata.

    Attributes:
        data: The formatted result data
        conceptIds: List of concept IDs in the result
        internalConnections: List of internal connection IDs
        linkers: List of linker IDs (connection IDs)
        reverse: List of reverse connection flags
        mainCompositionIds: List of main composition IDs
        countInfo: Count information strings
        isDataLoaded: Whether data has been loaded
        format: The output format used
        order: The sort order used
    """
    data: Any = None
    conceptIds: List[int] = field(default_factory=list)
    internalConnections: List[int] = field(default_factory=list)
    linkers: List[int] = field(default_factory=list)
    reverse: List[int] = field(default_factory=list)
    mainCompositionIds: List[int] = field(default_factory=list)
    countInfo: List[str] = field(default_factory=list)
    isDataLoaded: bool = False
    format: int = NORMAL
    order: str = "DESC"


async def schema_query_listener(
    query: FreeschemaQuery,
    token: str = ""
) -> SchemaQueryResult:
    """
    Execute a FreeSchema query and format results based on output format.

    This is the high-level wrapper function that handles result formatting
    based on the query's outputFormat setting. It first fetches raw data
    with ALLID format, then formats according to the original format.

    The formatting process converts graph data (concepts and connections)
    into nested JSON structures suitable for application consumption.

    Args:
        query: The FreeschemaQuery to execute
        token: Optional authentication token

    Returns:
        SchemaQueryResult containing formatted data and metadata

    Example:
        >>> query = FreeschemaQuery(
        ...     type="the_person",
        ...     inpage=20,
        ...     page=1,
        ...     outputFormat=DATAID
        ... )
        >>> result = await schema_query_listener(query)
        >>> print(f"Found {len(result.mainCompositionIds)} main compositions")
        >>> for item in result.data:
        ...     print(f"ID: {item['id']}, Data: {item['data']}")

    Example with nested queries:
        >>> query = FreeschemaQuery(
        ...     type="the_project",
        ...     freeschemaQueries=[
        ...         FreeschemaQuery(
        ...             type="the_task",
        ...             typeConnection="the_project_tasks"
        ...         )
        ...     ],
        ...     outputFormat=DATAV2
        ... )
        >>> result = await schema_query_listener(query)
    """
    from ccs.services.search.count_info import decode_count_info

    # Store original format
    original_format = query.outputFormat

    # Temporarily set to ALLID to get full data
    query.outputFormat = ALLID

    # Execute query
    raw_result = await freeschema_query_api(query, token)

    # Restore original format
    query.outputFormat = original_format

    # Build result object
    result = SchemaQueryResult(
        format=original_format,
        order=query.order,
    )

    if not raw_result:
        return result

    # Extract metadata from raw result
    if isinstance(raw_result, dict):
        result.conceptIds = raw_result.get("conceptIds", [])
        result.internalConnections = raw_result.get("internalConnections", [])
        result.linkers = raw_result.get("linkers", [])
        result.reverse = raw_result.get("reverse", [])
        result.mainCompositionIds = raw_result.get("mainCompositionIds", [])
        result.countInfo = raw_result.get("countinfo", [])
        result.isDataLoaded = True

        # Decode count information
        count_infos = decode_count_info(result.countInfo)

        # Format data based on original format
        if original_format == DATAID:
            from ccs.services.search.data_id_format import format_connections_data_id
            result.data = await format_connections_data_id(
                result.linkers,
                result.conceptIds,
                result.mainCompositionIds,
                result.reverse,
                count_infos,
                query.order
            )
        elif original_format == JUSTDATA:
            result.data = await _format_connections_just_data(
                result.linkers,
                result.conceptIds,
                result.mainCompositionIds,
                result.reverse,
                count_infos,
                query.order
            )
        elif original_format == DATAV2:
            result.data = await _format_connections_v2(
                result.linkers,
                result.conceptIds,
                result.mainCompositionIds,
                result.reverse,
                count_infos,
                query.order
            )
        else:
            # NORMAL or other formats - use basic formatting
            result.data = await _format_connections_normal(
                result.linkers,
                result.conceptIds,
                result.mainCompositionIds,
                result.reverse,
                count_infos
            )

    elif isinstance(raw_result, list):
        # If result is already a list, use as-is
        result.data = raw_result
        result.isDataLoaded = True

    return result


async def _format_connections_just_data(
    linkers: List[int],
    concept_ids: List[int],
    main_composition_ids: List[int],
    reverse: List[int],
    count_infos: List[Any],
    order: str = "DESC"
) -> List[Dict[str, Any]]:
    """
    Format results with just data, minimal metadata.

    Similar to DATAID but with simplified structure focusing on values.
    """
    from ccs.services.search.prefetch import get_connection_data_prefetch
    from ccs.services.search.ordering import order_connections
    from ccs.services.get.get_the_concept import GetTheConcept

    # Prefetch connections
    connections = await get_connection_data_prefetch(linkers)
    connections = order_connections(connections, order)

    # Build simplified data structure
    results: List[Dict[str, Any]] = []

    for main_id in main_composition_ids:
        concept = await GetTheConcept(main_id)
        if concept and concept.id != 0:
            item = {
                "id": main_id,
                "value": concept.characterValue,
                "type": concept.typeCharacter or (concept.type.characterValue if concept.type else ""),
            }
            results.append(item)

    return results


async def _format_connections_v2(
    linkers: List[int],
    concept_ids: List[int],
    main_composition_ids: List[int],
    reverse: List[int],
    count_infos: List[Any],
    order: str = "DESC"
) -> List[Dict[str, Any]]:
    """
    Format results in V2 format with full concept details.

    This is a modern format variant with comprehensive data.
    """
    from ccs.services.search.data_id_format import format_connections_data_id

    # V2 uses same logic as DATAID with additional processing
    return await format_connections_data_id(
        linkers,
        concept_ids,
        main_composition_ids,
        reverse,
        count_infos,
        order
    )


async def _format_connections_normal(
    linkers: List[int],
    concept_ids: List[int],
    main_composition_ids: List[int],
    reverse: List[int],
    count_infos: List[Any]
) -> List[Dict[str, Any]]:
    """
    Format results in standard NORMAL format.

    Basic format with essential concept information.
    """
    from ccs.services.get.get_the_concept import GetTheConcept

    results: List[Dict[str, Any]] = []

    for main_id in main_composition_ids:
        concept = await GetTheConcept(main_id)
        if concept and concept.id != 0:
            item = {
                "id": concept.id,
                "characterValue": concept.characterValue,
                "typeId": concept.typeId,
                "typeCharacter": concept.typeCharacter or (concept.type.characterValue if concept.type else ""),
                "userId": concept.userId,
                "categoryId": concept.categoryId,
                "accessId": concept.accessId,
                "isComposition": concept.isComposition,
            }
            results.append(item)

    return results
