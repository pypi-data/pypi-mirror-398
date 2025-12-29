"""
Create concept locally - creates concepts in local storage without backend sync.

This is the primary function for creating offline-first concepts.
"""

from datetime import datetime
from typing import Optional

from ccs.models.concept import Concept
from ccs.data.local_concept_data import LocalConceptsData
from ccs.data.local_id import LocalId
from ccs.data.inner_actions import InnerActions


async def CreateTheConceptLocal(
    referent: str,
    typecharacter: str,
    userId: int,
    categoryId: int,
    typeId: int,
    accessId: int,
    isComposition: bool = False,
    referentId: Optional[int] = 0,
    actions: Optional[InnerActions] = None
) -> Concept:
    """
    Creates a concept in local storage without syncing to the backend.

    This is the primary function for creating offline-first concepts. The concept
    is stored locally in memory, but NOT immediately sent to the backend.
    Sync happens later via the LocalSyncData class.

    **Virtual ID System:**
    - Generates a negative ID (e.g., -12345) to indicate local/virtual status
    - id and ghostId are initially equal and both negative
    - After backend sync: id becomes positive (real backend ID)
    - ghostId remains negative (preserves original local ID)

    **Special Case:**
    If referent is "the", returns a special concept with id=1 (system concept).

    Args:
        referent: The character value (text/name) of the concept.
                 This is the human-readable content.
        typecharacter: The type name as a string (e.g., "the_note", "the_person").
        userId: The ID of the user creating this concept.
        categoryId: The category classification ID.
        typeId: The type classification ID.
        accessId: Access control level (e.g., 1=Public, 2=Private).
        isComposition: True if this concept represents a composition root.
        referentId: Optional reference to another concept ID.
        actions: Action tracking object for batch operations.

    Returns:
        The created Concept object with a negative ID.

    Example:
        >>> draftNote = await CreateTheConceptLocal(
        ...     referent="Meeting Notes - Draft",
        ...     typecharacter="the_note",
        ...     userId=101,
        ...     categoryId=1,
        ...     typeId=3,
        ...     accessId=2
        ... )
        >>> print(draftNote.id)  # -1 (negative = local)

    Example:
        >>> # Track actions for batch operations
        >>> actions = InnerActions()
        >>> concept1 = await CreateTheConceptLocal(
        ...     "Item 1", "the_item", 101, 1, 4, 2, actions=actions
        ... )
        >>> print(len(actions.concepts))  # 1
    """
    if actions is None:
        actions = InnerActions()

    # Special case: "the" is the root system concept
    if referent == "the":
        concept = Concept(
            id=1,
            userId=999,
            typeId=5,
            categoryId=5,
            referentId=referentId,
            characterValue=referent,
            accessId=accessId,
            isNew=True,
            entryTimeStamp=datetime.now(),
            updatedTimeStamp=datetime.now(),
            typeCharacter=typecharacter
        )
        return concept

    # Generate a unique negative ID for local concept
    conceptId = LocalId.get_concept_id()

    # Create the concept
    concept = Concept(
        id=conceptId,
        userId=userId,
        typeId=typeId,
        categoryId=categoryId,
        referentId=referentId,
        characterValue=referent,
        accessId=accessId,
        isNew=True,
        entryTimeStamp=datetime.now(),
        updatedTimeStamp=datetime.now(),
        typeCharacter=typecharacter
    )

    # Mark as temporary/local
    concept.isTemp = True
    concept.isComposition = isComposition

    # Add to local storage
    LocalConceptsData.AddConcept(concept)

    # Track in actions
    actions.concepts.append(concept)

    return concept
