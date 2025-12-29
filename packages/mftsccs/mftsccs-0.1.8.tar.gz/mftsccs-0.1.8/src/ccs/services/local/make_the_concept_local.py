"""
Make concept locally - implements get-or-create pattern for local concepts.
"""

from typing import Optional

from ccs.models.concept import Concept
from ccs.data.local_concept_data import LocalConceptsData
from ccs.data.inner_actions import InnerActions
from ccs.services.local.create_the_concept_local import CreateTheConceptLocal


async def MakeTheConceptLocal(
    referent: str,
    typeCharacter: str,
    userId: int,
    categoryId: int,
    typeId: int,
    actions: Optional[InnerActions] = None
) -> Concept:
    """
    Gets or creates a local concept - implements get-or-create pattern.

    Checks LocalConceptsData for existing concept matching referent and typeId.
    If found, returns existing concept. If not found, creates new local concept.

    **Special Case**: If typeCharacter is "the", sets categoryId to 1 (system category).

    Args:
        referent: The character value/name of the concept.
        typeCharacter: Type name string (e.g., "the_name").
        userId: User ID creating the concept.
        categoryId: Category classification ID.
        typeId: Type classification ID.
        actions: Action tracking for batch operations.

    Returns:
        Existing or newly created Concept.

    Example:
        >>> concept = await MakeTheConceptLocal(
        ...     "Active", "the_status", 101, 1, 5
        ... )
        >>> # Returns existing "Active" status or creates new one
    """
    if actions is None:
        actions = InnerActions()

    # Check for existing concept with same referent and type
    concept = LocalConceptsData.GetConceptByCharacterAndTypeLocal(
        referent, typeId
    )

    accessId = 4

    # Special case: root type "the" uses category 1
    if typeCharacter == "the":
        categoryId = 1

    # If not found (id == 0), create new concept
    if concept.id == 0:
        concept = await CreateTheConceptLocal(
            referent=referent,
            typecharacter=typeCharacter,
            userId=userId,
            categoryId=categoryId,
            typeId=typeId,
            accessId=accessId,
            isComposition=False,
            referentId=None,
            actions=actions
        )

    return concept
