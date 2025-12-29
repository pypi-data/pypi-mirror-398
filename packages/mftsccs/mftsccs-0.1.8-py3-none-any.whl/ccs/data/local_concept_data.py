"""
Local concept data storage - manages concepts in local memory.

Provides binary tree-based indexing for fast lookups by ID, character value,
and type. This is the Python equivalent of LocalConceptsData from the JS library.
"""

from typing import Dict, List, Optional
from ccs.models.concept import Concept, create_default_concept


class LocalConceptsData:
    """
    Manages local concept storage with multiple indexing strategies.

    Uses dictionaries as simplified binary trees for fast lookups:
    - By ID (primary index)
    - By character value (for deduplication)
    - By type ID (for type-based queries)
    - By character + type combination (for exact match)

    This is an in-memory store that can later be backed by SQLite or similar.

    Example:
        >>> LocalConceptsData.AddConcept(my_concept)
        >>> found = LocalConceptsData.GetConcept(concept_id)
        >>> by_type = LocalConceptsData.GetConceptsByTypeId(51)
    """

    # Primary storage - indexed by concept ID
    _concepts_by_id: Dict[int, Concept] = {}

    # Character value index - maps characterValue to list of concepts
    _concepts_by_character: Dict[str, List[Concept]] = {}

    # Type index - maps typeId to list of concepts
    _concepts_by_type: Dict[int, List[Concept]] = {}

    # Combined index - maps (characterValue, typeId) to concept
    _concepts_by_char_type: Dict[tuple, Concept] = {}

    @classmethod
    def AddConcept(cls, concept: Concept) -> None:
        """
        Add a concept to local storage with all indexes.

        Args:
            concept: The Concept to store.
        """
        if concept.id == 0:
            return

        # Primary index
        cls._concepts_by_id[concept.id] = concept

        # Character value index
        char_val = concept.characterValue
        if char_val not in cls._concepts_by_character:
            cls._concepts_by_character[char_val] = []
        cls._concepts_by_character[char_val].append(concept)

        # Type index
        typeId = concept.typeId
        if typeId not in cls._concepts_by_type:
            cls._concepts_by_type[typeId] = []
        cls._concepts_by_type[typeId].append(concept)

        # Combined character + type index
        cls._concepts_by_char_type[(char_val, typeId)] = concept

    @classmethod
    def GetConcept(cls, conceptId: int) -> Concept:
        """
        Get a concept by its ID.

        Args:
            conceptId: The ID of the concept to retrieve.

        Returns:
            The Concept if found, or a default concept with id=0.
        """
        return cls._concepts_by_id.get(conceptId, create_default_concept())

    @classmethod
    def GetConceptByCharacter(cls, characterValue: str) -> Concept:
        """
        Get a concept by its character value.

        Args:
            characterValue: The character value to search for.

        Returns:
            The first matching Concept, or a default concept with id=0.
        """
        concepts = cls._concepts_by_character.get(characterValue, [])
        return concepts[0] if concepts else create_default_concept()

    @classmethod
    def GetConceptByCharacterAndTypeLocal(
        cls, characterValue: str, typeId: int
    ) -> Concept:
        """
        Get a concept by character value and type ID.

        This is the key function for deduplication - finds existing concepts
        with the same value and type.

        Args:
            characterValue: The character value to search for.
            typeId: The type ID to match.

        Returns:
            The matching Concept, or a default concept with id=0 and userId=0.
        """
        return cls._concepts_by_char_type.get(
            (characterValue, typeId),
            create_default_concept()
        )

    @classmethod
    def GetConceptByCharacterAndCategoryLocal(
        cls, characterValue: str, categoryId: int
    ) -> Concept:
        """
        Get a concept by character value and category ID.

        Args:
            characterValue: The character value to search for.
            categoryId: The category ID to match.

        Returns:
            The matching Concept, or a default concept with id=0.
        """
        concepts = cls._concepts_by_character.get(characterValue, [])
        for concept in concepts:
            if concept.categoryId == categoryId:
                return concept
        return create_default_concept()

    @classmethod
    def GetConceptsByTypeId(cls, typeId: int) -> List[Concept]:
        """
        Get all concepts with a specific type ID.

        Args:
            typeId: The type ID to filter by.

        Returns:
            List of matching Concepts.
        """
        return cls._concepts_by_type.get(typeId, [])

    @classmethod
    def GetConceptsByTypeIdAndUser(
        cls, typeId: int, userId: int
    ) -> List[Concept]:
        """
        Get all concepts with a specific type ID and user ID.

        Args:
            typeId: The type ID to filter by.
            userId: The user ID to filter by.

        Returns:
            List of matching Concepts.
        """
        concepts = cls._concepts_by_type.get(typeId, [])
        return [c for c in concepts if c.userId == userId]

    @classmethod
    def RemoveConcept(cls, concept: Concept) -> None:
        """
        Remove a concept from all indexes.

        Args:
            concept: The Concept to remove.
        """
        if concept.id == 0:
            return

        # Remove from primary index
        cls._concepts_by_id.pop(concept.id, None)

        # Remove from character index
        char_val = concept.characterValue
        if char_val in cls._concepts_by_character:
            cls._concepts_by_character[char_val] = [
                c for c in cls._concepts_by_character[char_val]
                if c.id != concept.id
            ]

        # Remove from type index
        typeId = concept.typeId
        if typeId in cls._concepts_by_type:
            cls._concepts_by_type[typeId] = [
                c for c in cls._concepts_by_type[typeId]
                if c.id != concept.id
            ]

        # Remove from combined index
        cls._concepts_by_char_type.pop((char_val, typeId), None)

    @classmethod
    def RemoveConceptById(cls, conceptId: int) -> None:
        """
        Remove a concept by its ID.

        Args:
            conceptId: The ID of the concept to remove.
        """
        concept = cls.GetConcept(conceptId)
        if concept.id != 0:
            cls.RemoveConcept(concept)

    @classmethod
    def ClearData(cls) -> None:
        """Clear all stored concepts."""
        cls._concepts_by_id.clear()
        cls._concepts_by_character.clear()
        cls._concepts_by_type.clear()
        cls._concepts_by_char_type.clear()

    @classmethod
    def UpdateConceptSyncStatus(cls, conceptId: int) -> None:
        """
        Mark a concept as synced.

        Args:
            conceptId: The ID of the concept to update.
        """
        if conceptId in cls._concepts_by_id:
            cls._concepts_by_id[conceptId].isSynced = True
