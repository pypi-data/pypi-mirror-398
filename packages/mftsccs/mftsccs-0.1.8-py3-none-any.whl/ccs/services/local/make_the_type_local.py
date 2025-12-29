"""
Make type concept locally - handles hierarchical type system creation.

Type concepts are placeholders/templates (e.g., "the_first_name", "the_email")
that define what kind of data a concept represents.
"""

from typing import Optional

from ccs.models.concept import Concept
from ccs.data.inner_actions import InnerActions
from ccs.services.local.helpers import SplitStrings
from ccs.services.local.get_concept_by_character_local import (
    GetConceptByCharacterAndCategoryLocal
)
from ccs.services.local.make_the_concept_local import MakeTheConceptLocal
from ccs.services.local.create_the_concept_local import CreateTheConceptLocal


async def MakeTheTypeConceptLocal(
    typeString: str,
    sessionId: int,
    sessionUserId: int,
    userId: int,
    actions: Optional[InnerActions] = None
) -> Concept:
    """
    Creates or retrieves a type concept locally - handles hierarchical type system.

    Type concepts are placeholders/templates (e.g., "the_first_name", "the_email")
    that define what kind of data a concept represents. They have no actual value.

    **Hierarchical Processing (Complex Logic)**:
    - Single word (e.g., "status"): Creates simple type concept with typeId=51
    - Compound words (e.g., "the_person_email"): Splits into parts and creates hierarchy:
      1. Creates category concept from first part ("the_person")
      2. Creates type concept from second part ("email")
      3. Creates final concept with category and type linked
      **Uses recursion** to build multi-level type hierarchies

    Always checks for existing type concept before creating to prevent duplicates.

    Args:
        typeString: The type name to create (e.g., "the_status", "the_person_email")
        sessionId: Session identifier (typically 999)
        sessionUserId: Session user ID (typically 999, not used)
        userId: User creating the type concept
        actions: Action tracking for batch operations

    Returns:
        Type Concept (existing or newly created)

    Example:
        >>> # Simple type
        >>> statusType = await MakeTheTypeConceptLocal(
        ...     "the_status", 999, 999, 101
        ... )
        >>> # Creates: "the_status" type concept

    Example:
        >>> # Hierarchical type (recursive processing)
        >>> emailType = await MakeTheTypeConceptLocal(
        ...     "the_person_email", 999, 999, 101
        ... )
        >>> # Creates: "the_person" (category) + "email" (type) + "the_person_email" (combined)
    """
    if actions is None:
        actions = InnerActions()

    accessId = 4

    # Check if type concept already exists
    existingConcept = await GetConceptByCharacterAndCategoryLocal(typeString)

    # If concept exists (id != 0 and userId != 0), return it
    if existingConcept.id != 0 and existingConcept.userId != 0:
        return existingConcept

    # Need to create the type concept
    # Split the type string to check for hierarchical types
    splittedStringArray = SplitStrings(typeString)

    if splittedStringArray[0] == typeString:
        # Single word type (no underscore found, or just one part)
        # Create simple type concept with typeId=51
        concept = await MakeTheConceptLocal(
            referent=typeString,
            typeCharacter="the",
            userId=userId,
            categoryId=1,
            typeId=51,
            actions=actions
        )
        return concept
    else:
        # Compound type (e.g., "the_person_email" -> ["the_person", "email"])
        # Recursively create category and type concepts

        # Create/get category concept (e.g., "the_person")
        categoryConcept = await MakeTheTypeConceptLocal(
            splittedStringArray[0],
            sessionId,
            sessionUserId,
            userId,
            actions
        )

        # Create/get type concept (e.g., "email" -> "the_email" if needed)
        typeConcept = await MakeTheTypeConceptLocal(
            splittedStringArray[1],
            sessionId,
            sessionUserId,
            userId,
            actions
        )

        # Create the combined concept (e.g., "the_person_email")
        # Uses categoryConcept.id as categoryId and typeConcept.id as typeId
        concept = await CreateTheConceptLocal(
            referent=typeString,
            typecharacter=splittedStringArray[1],
            userId=userId,
            categoryId=categoryConcept.id,
            typeId=typeConcept.id,
            accessId=accessId,
            isComposition=False,
            referentId=None,
            actions=actions
        )

        return concept
