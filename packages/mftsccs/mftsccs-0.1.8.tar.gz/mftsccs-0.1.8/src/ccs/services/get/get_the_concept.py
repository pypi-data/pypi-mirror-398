"""
GetTheConcept - Primary function for fetching concepts with caching and multi-source lookup.
"""

import asyncio
from typing import Dict, Optional

from ccs.models.concept import Concept, create_default_concept
from ccs.data.local_concept_data import LocalConceptsData
from ccs.api.get_concept import GetConcept


# Promise cache to prevent duplicate concurrent requests
_concept_cache: Dict[int, asyncio.Task] = {}


async def GetTheConcept(id: int, userId: int = 999) -> Concept:
    """
    Retrieves a concept by its ID with intelligent caching and multi-source lookup.

    This is the primary function for fetching concepts in the system. It implements
    a sophisticated multi-level retrieval strategy:

    **Retrieval Strategy:**
    1. Checks in-memory task cache to prevent duplicate requests
    2. For negative IDs: Fetches from local storage (LocalConceptsData)
    3. For positive IDs: Checks local cache first
    4. If not in cache: Fetches from backend API
    5. Automatically resolves and attaches the concept's type information

    **Features:**
    - Task caching prevents duplicate concurrent requests for the same concept
    - Automatic type resolution (fetches and attaches type concept)
    - Supports both server concepts (positive IDs) and local concepts (negative IDs)

    Args:
        id: The unique identifier of the concept to retrieve.
            Positive IDs = server concepts, Negative IDs = local-only concepts
        userId: The ID of the user requesting the concept. Used for access tracking.
                Defaults to 999 (system/anonymous user)

    Returns:
        The Concept object if found, or a default empty Concept if not found.

    Example:
        >>> # Get a server concept
        >>> concept = await GetTheConcept(12345, 101)
        >>> print(concept.characterValue)  # "Alice Smith"
        >>> print(concept.type.characterValue)  # "Person" (auto-resolved)

    Example:
        >>> # Get a local concept (negative ID)
        >>> localConcept = await GetTheConcept(-5, 101)
        >>> print(localConcept.characterValue)  # "Local Draft"

    Example:
        >>> # Multiple concurrent calls use the same task (efficient)
        >>> results = await asyncio.gather(
        ...     GetTheConcept(123),
        ...     GetTheConcept(123),  # Same ID - uses cached task
        ...     GetTheConcept(123)   # Same ID - uses cached task
        ... )
        >>> # Only one actual fetch is performed
    """
    concept = create_default_concept()

    # Check the task cache for in-flight requests
    if id in _concept_cache:
        try:
            return await _concept_cache[id]
        except Exception:
            # If cached task failed, continue with new fetch
            pass

    # Create new fetch task
    async def _fetch_concept() -> Concept:
        try:
            nonlocal concept

            # For negative IDs, fetch from local storage
            if id < 0:
                localConcept = LocalConceptsData.GetConceptByGhostId(id)
                if localConcept:
                    return localConcept
                return concept

            # For positive IDs, check local cache first
            concept = LocalConceptsData.GetConcept(id)

            # If not in cache, fetch from API
            if concept is None or concept.id == 0:
                concept = await GetConcept(id)

            # Auto-resolve type information
            if concept.id != 0 and concept.type is None:
                await AddTypeConcept(concept)

            return concept

        except Exception as err:
            print(f"Error in GetTheConcept: {err}")
            return create_default_concept()

        finally:
            # Remove from cache after completion
            _concept_cache.pop(id, None)

    # Create and cache the task
    task = asyncio.create_task(_fetch_concept())
    _concept_cache[id] = task

    return await task


async def AddTypeConcept(concept: Concept) -> None:
    """
    Fetches and attaches type information to a concept if not already present.

    This utility function ensures that a concept has its type information loaded
    and attached. Every concept has a `typeId` that references another concept
    representing its type (e.g., a person concept might have typeId=1 which
    points to a "Person" type concept).

    **Process:**
    1. Checks if concept.type is already set (if yes, does nothing)
    2. Attempts to fetch type concept from local cache
    3. If not in cache and typeId is valid: fetches from backend API
    4. Attaches the type concept to concept.type property

    **Type Concept:**
    A type concept is a special concept that represents a classification or category.
    For example: "Person", "Document", "Organization" are type concepts.

    Args:
        concept: The concept object to which type information should be added.
                The concept must have a valid `typeId` property.

    Returns:
        None. The concept.type property is modified in place.

    Example:
        >>> concept = await GetTheConcept(12345)
        >>> print(concept.type)  # might be None
        >>>
        >>> await AddTypeConcept(concept)
        >>> print(concept.type.characterValue)  # "Person"

    Example:
        >>> # Ensure multiple concepts have their types loaded
        >>> concepts = [await GetTheConcept(id) for id in [1, 2, 3, 4, 5]]
        >>> await asyncio.gather(*[AddTypeConcept(c) for c in concepts])
        >>> # All concepts now have their type information
    """
    if concept.type is not None:
        return

    # Skip invalid typeIds
    if concept.typeId == 0 or concept.typeId == 999:
        return

    # Try to get type from local cache first
    typeConcept = LocalConceptsData.GetConcept(concept.typeId)

    if typeConcept is None or typeConcept.id == 0:
        # Fetch from API
        typeConcept = await GetConcept(concept.typeId)

    if typeConcept and typeConcept.id != 0:
        concept.type = typeConcept


def ClearConceptCache() -> None:
    """
    Clears the in-memory concept cache.

    Use this when you need to force fresh fetches of all concepts.
    """
    _concept_cache.clear()
