"""
Concept model - the core building block of the concept-connection system.

A Concept represents an entity/node in the knowledge graph with properties
like type, value, ownership, and access control.

Note: Uses camelCase for API compatibility with the backend.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


@dataclass
class Concept:
    """
    Represents a concept in the knowledge graph.

    Concepts are the fundamental building blocks that can be connected
    to form complex data structures and relationships.

    Note: Property names use camelCase to match the backend API.

    Attributes:
        id: Unique identifier. Negative IDs indicate local/virtual concepts.
        userId: ID of the user who owns this concept.
        typeId: ID of the type concept that defines what kind of data this is.
        categoryId: Category classification ID for further classification.
        referentId: Optional reference to another concept ID.
        characterValue: The actual value/content of the concept.
        accessId: Access control level (e.g., 1=Public, 2=Private, 4=Default).
        isNew: Whether this concept was recently created.
        entryTimeStamp: When the concept was created.
        updatedTimeStamp: When the concept was last updated.
        typeCharacter: The type name as a string (e.g., "the_name").
        ghostId: Preserves original local ID after sync (for mapping).
        isComposition: Whether this is a composition root concept.
        isTemp: Whether this is a temporary/local concept.
        isSynced: Whether this concept has been synced to the backend.
        type: Reference to the type Concept object.
        referent: Reference to the referent Concept object.

    Example:
        >>> concept = Concept(
        ...     id=-12345,
        ...     userId=101,
        ...     typeId=51,
        ...     categoryId=1,
        ...     referentId=0,
        ...     characterValue="Alice",
        ...     accessId=4,
        ...     typeCharacter="the_name"
        ... )
    """

    id: int
    userId: int
    typeId: int
    categoryId: int
    referentId: Optional[int]
    characterValue: str
    accessId: int
    isNew: bool = False
    entryTimeStamp: datetime = field(default_factory=datetime.now)
    updatedTimeStamp: datetime = field(default_factory=datetime.now)
    typeCharacter: str = ""
    ghostId: int = field(init=False)
    isComposition: bool = False
    isTemp: bool = False
    isSynced: bool = False
    type: Optional["Concept"] = None
    referent: Optional["Concept"] = None
    count: int = 0
    applicationId: int = 0
    x: int = 0
    y: int = 0

    def __post_init__(self):
        """Set ghostId to match id initially."""
        self.ghostId = self.id

    def getType(self) -> int:
        """Return the type ID of this concept."""
        return self.typeId

    def __repr__(self) -> str:
        return (
            f"Concept(id={self.id}, characterValue='{self.characterValue}', "
            f"typeCharacter='{self.typeCharacter}', userId={self.userId})"
        )


def create_default_concept() -> Concept:
    """
    Create a default/empty concept with zero values.

    Used as a placeholder when no concept is found.

    Returns:
        A Concept with id=0 and userId=0 indicating "not found".
    """
    return Concept(
        id=0,
        userId=0,
        typeId=0,
        categoryId=0,
        referentId=0,
        characterValue="",
        accessId=0,
        typeCharacter=""
    )
