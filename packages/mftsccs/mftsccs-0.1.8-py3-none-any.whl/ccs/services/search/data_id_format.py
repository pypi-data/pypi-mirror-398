"""
DataIdFormat - Formatting functions for converting graph data to JSON.

This module implements the three-pass formatting process for converting
concepts and connections into nested JSON structures.

The format produces output like:
[
    {
        "id": 123,
        "data": {
            "the_person": {
                "the_name": {"id": 1, "data": {"the_name": "John"}},
                "the_email": {"id": 2, "data": {"the_email": "john@example.com"}}
            }
        },
        "created_on": "2024-01-01T00:00:00"
    }
]
"""

from typing import Any, Dict, List
from ccs.models.connection import Connection
from ccs.services.search.count_info import CountInfo


async def format_connections_data_id(
    linkers: List[int],
    concept_ids: List[int],
    main_composition_ids: List[int],
    reverse: List[int],
    count_infos: List[CountInfo],
    order: str = "DESC"
) -> List[Dict[str, Any]]:
    """
    Main entry point for formatting connections to DATA-ID format.

    This function converts graph concepts and connections to a nested JSON format
    that includes both IDs and data for each concept.

    Args:
        linkers: List of connection IDs (linker connections)
        concept_ids: List of concept IDs in the result
        main_composition_ids: List of main composition IDs (root entities)
        reverse: List of connection IDs that should be processed in reverse
        count_infos: List of CountInfo objects for aggregation data
        order: Sort order - "ASC" or "DESC"

    Returns:
        List of formatted composition dictionaries

    Example:
        >>> result = await format_connections_data_id(
        ...     linkers=[1, 2, 3],
        ...     concept_ids=[100, 101, 102],
        ...     main_composition_ids=[100],
        ...     reverse=[],
        ...     count_infos=[],
        ...     order="DESC"
        ... )
        >>> print(result[0]["id"])  # 100
    """
    from ccs.services.search.prefetch import get_connection_data_prefetch
    from ccs.services.search.ordering import order_connections

    # Step 1: Prefetch all connections and related concepts
    prefetch_connections = await get_connection_data_prefetch(linkers)

    # Step 2: Order connections
    prefetch_connections = order_connections(prefetch_connections, order)

    # Step 3: Initialize composition data structures (Pass 1)
    composition_data: Dict[int, Any] = {}
    composition_data = await format_function_data(prefetch_connections, composition_data, reverse)

    # Step 4: Add nested data with IDs (Pass 2)
    composition_data = await format_function_data_for_data(prefetch_connections, composition_data, reverse)

    # Step 5: Stitch together final output (Pass 3)
    output = await format_from_connections_altered_array_external(
        prefetch_connections,
        composition_data,
        main_composition_ids,
        reverse
    )

    return output


async def format_function_data(
    connections: List[Connection],
    composition_data: Dict[int, Any],
    reverse: List[int]
) -> Dict[int, Any]:
    """
    Pass 1: Initialize empty concept structures indexed by ID.

    This pass creates the basic structure for each concept, initializing
    empty dictionaries keyed by the concept's type.

    Args:
        connections: List of prefetched connections
        composition_data: Dictionary to populate (mutated in place)
        reverse: List of connection IDs to process in reverse

    Returns:
        Updated composition_data dictionary
    """
    from ccs.services.get.get_the_concept import GetTheConcept

    for connection in connections:
        reverse_flag = connection.id in reverse

        of_concept = await GetTheConcept(connection.ofTheConceptId)
        to_concept = await GetTheConcept(connection.toTheConceptId)

        if of_concept.id == 0 or to_concept.id == 0:
            continue

        if reverse_flag:
            # Reverse direction: to -> from
            key = to_concept.type.characterValue if to_concept.type else "self"

            if to_concept.id not in composition_data:
                composition_data[to_concept.id] = {}

            if key not in composition_data[to_concept.id]:
                composition_data[to_concept.id][key] = {}

            # Also initialize the of_concept
            if of_concept.id not in composition_data:
                composition_data[of_concept.id] = {}
        else:
            # Forward direction: from -> to
            key = of_concept.type.characterValue if of_concept.type else "self"

            if of_concept.id not in composition_data:
                composition_data[of_concept.id] = {}

            if key not in composition_data[of_concept.id]:
                composition_data[of_concept.id][key] = {}

            # Also initialize the to_concept
            if to_concept.id not in composition_data:
                composition_data[to_concept.id] = {}

    return composition_data


def _remove_the_prefix(s: str) -> str:
    """Remove 'the_' prefix from a string if present."""
    if s.startswith("the_"):
        return s[4:]
    return s


def _is_numeric_string(s: str) -> bool:
    """Check if a string is numeric (matches isNaN(Number(x)) === false in JS)."""
    if not s:
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False


async def format_function_data_for_data(
    connections: List[Connection],
    composition_data: Dict[int, Any],
    reverse: List[int]
) -> Dict[int, Any]:
    """
    Pass 2: Add detailed data properties with ID and data structure.

    This pass populates the nested data structure with actual concept values,
    creating objects with "id" and "data" keys.

    Args:
        connections: List of prefetched connections
        composition_data: Dictionary to update (mutated in place)
        reverse: List of connection IDs to process in reverse

    Returns:
        Updated composition_data dictionary
    """
    from ccs.services.get.get_the_concept import GetTheConcept

    for connection in connections:
        reverse_flag = connection.id in reverse

        of_concept = await GetTheConcept(connection.ofTheConceptId)
        to_concept = await GetTheConcept(connection.toTheConceptId)
        linker_concept = await GetTheConcept(connection.typeId)

        if of_concept.id == 0 or to_concept.id == 0:
            continue

        # Get the linker/connection type name
        data_character = linker_concept.characterValue if linker_concept and linker_concept.id != 0 else ""

        if reverse_flag:
            # Reverse direction: to -> from
            key = to_concept.type.characterValue if to_concept.type else "self"
            my_type = of_concept.type.characterValue if of_concept.type else "none"
            value = of_concept.characterValue

            # If no connection type defined, use the type of the destination concept
            if data_character == "":
                data_character = my_type
                data_character = _remove_the_prefix(data_character)

            reverse_character = f"{data_character}_reverse"

            # Skip _s_ type connections for data (they're composition links)
            if "_s_" in reverse_character:
                continue

            # Build the data object
            data = {
                "id": of_concept.id,
                "data": {my_type: value}
            }

            # Add to composition
            if to_concept.id in composition_data:
                if key not in composition_data[to_concept.id]:
                    composition_data[to_concept.id][key] = {}

                target = composition_data[to_concept.id][key]
                # Convert string to dict if needed
                if isinstance(target, str):
                    composition_data[to_concept.id][key] = {}
                    target = composition_data[to_concept.id][key]

                if isinstance(target, dict):
                    target[reverse_character] = data
        else:
            # Forward direction: from -> to
            key = of_concept.type.characterValue if of_concept.type else "self"
            my_type = to_concept.type.characterValue if to_concept.type else "none"
            value = to_concept.characterValue

            # If no connection type defined, use the type of the destination concept
            if data_character == "":
                data_character = my_type
                data_character = _remove_the_prefix(data_character)

            # Build the data object
            data = {
                "id": to_concept.id,
                "data": {my_type: value}
            }

            # Handle based on data_character type
            if of_concept.id in composition_data:
                if key not in composition_data[of_concept.id]:
                    composition_data[of_concept.id][key] = {}

                target = composition_data[of_concept.id][key]

                # Convert string to dict if needed
                if isinstance(target, str):
                    composition_data[of_concept.id][key] = {}
                    target = composition_data[of_concept.id][key]

                # Check if data_character is NOT a number (isNaN in JS)
                if not _is_numeric_string(data_character):
                    # Skip _s_ type connections for data
                    if "_s_" not in data_character:
                        if isinstance(target, dict):
                            target[data_character] = data
                else:
                    # Numeric data_character - use array
                    if isinstance(target, list):
                        target.append(data)
                    else:
                        composition_data[of_concept.id][key] = [data]

    return composition_data


async def format_from_connections_altered_array_external(
    connections: List[Connection],
    composition_data: Dict[int, Any],
    main_composition_ids: List[int],
    reverse: List[int]
) -> List[Dict[str, Any]]:
    """
    Pass 3: Stitch compositions together with timestamps and create final output.

    This pass links child compositions to parent compositions and builds
    the final array of main composition objects.

    Args:
        connections: List of prefetched connections
        composition_data: Dictionary of composition data from previous passes
        main_composition_ids: List of IDs for the main/root compositions
        reverse: List of connection IDs to process in reverse

    Returns:
        List of formatted main composition dictionaries
    """
    from ccs.services.get.get_the_concept import GetTheConcept

    for connection in connections:
        reverse_flag = connection.id in reverse

        of_concept = await GetTheConcept(connection.ofTheConceptId)
        to_concept = await GetTheConcept(connection.toTheConceptId)
        linker_concept = await GetTheConcept(connection.typeId)

        if of_concept.id == 0 or to_concept.id == 0:
            continue

        if reverse_flag:
            # Reverse direction: to -> from
            if to_concept.id in composition_data:
                key = to_concept.type.characterValue if to_concept.type else "self"

                # Initialize or get target
                if to_concept.id in composition_data:
                    new_data = composition_data[to_concept.id]
                    # Convert string to dict if needed
                    if isinstance(new_data.get(key), str):
                        new_data[key] = {}
                else:
                    new_data = {key: {}}
                    composition_data[to_concept.id] = new_data

                if key not in new_data:
                    new_data[key] = {}

                # Check if ofTheConcept has composition data
                is_comp = composition_data.get(of_concept.id)
                if is_comp:
                    # Get timestamp
                    created_on = connection.entryTimeStamp

                    # Build linked data with nested composition
                    linked_data = {
                        "id": of_concept.id,
                        "data": composition_data[of_concept.id],
                        "created_on": created_on
                    }

                    reverse_character = f"{linker_concept.characterValue}_reverse"

                    target = new_data[key]
                    if isinstance(target.get(reverse_character), list):
                        target[reverse_character].append(linked_data)
                    else:
                        if "_s_" in reverse_character:
                            target[reverse_character] = [linked_data]
                        else:
                            target[reverse_character] = linked_data
        else:
            # Forward direction: from -> to
            if of_concept.id in composition_data:
                key = of_concept.type.characterValue if of_concept.type else "self"

                # Initialize or get target
                if of_concept.id in composition_data:
                    new_data = composition_data[of_concept.id]
                    # Convert string to dict if needed
                    if isinstance(new_data.get(key), str):
                        new_data[key] = {}
                else:
                    new_data = {key: {}}
                    composition_data[of_concept.id] = new_data

                if key not in new_data:
                    new_data[key] = {}

                # Determine linker concept value with fallbacks
                linker_concept_value = linker_concept.characterValue if linker_concept and linker_concept.id != 0 else ""
                if linker_concept_value == "":
                    linker_concept_value = to_concept.characterValue
                if linker_concept_value == "":
                    linker_concept_value = to_concept.type.characterValue if to_concept.type else ""

                # Check if toTheConcept has composition data
                my_data = composition_data.get(to_concept.id)
                if my_data:
                    # Get timestamp
                    created_on = connection.entryTimeStamp

                    # Build linked data with nested composition
                    linked_data = {
                        "id": to_concept.id,
                        "data": composition_data[to_concept.id],
                        "created_on": created_on
                    }

                    target = new_data[key]

                    # Check if target[key] is already an array at top level
                    if isinstance(target, list):
                        target.append(my_data)
                    elif isinstance(target.get(linker_concept_value), list):
                        target[linker_concept_value].append(linked_data)
                    else:
                        if "_s_" in linker_concept_value:
                            target[linker_concept_value] = [linked_data]
                        else:
                            target[linker_concept_value] = linked_data

    # Build final output for main compositions
    main_data: List[Dict[str, Any]] = []

    for main_id in main_composition_ids:
        main_item = {
            "id": main_id,
            "data": composition_data.get(main_id, {}),
        }
        main_data.append(main_item)

    return main_data
