"""
Get concept by character locally - retrieves concepts by character value and category.
"""

from ccs.models.concept import Concept
from ccs.data.local_concept_data import LocalConceptsData


async def GetConceptByCharacterAndCategoryLocal(
    characterValue: str,
    categoryId: int = 0
) -> Concept:
    """
    Get a concept by its character value and optionally category.

    If categoryId is not provided (0), returns first match by character value.
    If categoryId is provided, returns concept matching both.

    Args:
        characterValue: The character value to search for.
        categoryId: Optional category ID to filter by.

    Returns:
        Matching Concept or default concept with id=0.
    """
    if categoryId == 0:
        return LocalConceptsData.GetConceptByCharacter(characterValue)
    else:
        return LocalConceptsData.GetConceptByCharacterAndCategoryLocal(
            characterValue, categoryId
        )
