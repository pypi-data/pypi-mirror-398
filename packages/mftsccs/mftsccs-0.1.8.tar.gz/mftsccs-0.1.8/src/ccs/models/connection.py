"""
Connection model - represents relationships between concepts.

A Connection links two concepts together with a specific type and order.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ccs.models.concept import Concept


@dataclass
class Connection:
    """
    Represents a connection/relationship between two concepts.

    Connections are the edges in the knowledge graph that link
    concepts together with typed relationships.

    Note: Property names use camelCase to match the backend API.

    Attributes:
        id: Unique identifier. Negative IDs indicate local/virtual connections.
        ofTheConceptId: ID of the source concept ("from" concept).
        toTheConceptId: ID of the target concept ("to" concept).
        userId: ID of the user who owns this connection.
        typeId: ID of the type concept defining the relationship type.
        orderId: Order/sequence number for ordered relationships.
        accessId: Access control level.
        ghostId: Preserves original local ID after sync.
        typeCharacter: The type name as a string.
        entryTimeStamp: When the connection was created.
        terminationDateTime: When the connection was terminated (if applicable).
        localSyncTime: When the connection was last synced locally.
        isTemp: Whether this is a temporary/local connection.
        toUpdate: Whether this connection needs to be updated.
        applicationId: Application identifier for multi-app scenarios.
        type: Reference to the type Concept object.
        ofConcept: Reference to the source Concept object.
        toConcept: Reference to the target Concept object.

    Example:
        >>> connection = Connection(
        ...     id=-1,
        ...     ofTheConceptId=100,
        ...     toTheConceptId=200,
        ...     userId=101,
        ...     typeId=50,
        ...     orderId=1,
        ...     accessId=4
        ... )
    """

    id: int
    ofTheConceptId: int
    toTheConceptId: int
    userId: int
    typeId: int
    orderId: int = 1
    accessId: int = 4
    count: int = 0
    ghostId: int = field(init=False)
    typeCharacter: str = ""
    entryTimeStamp: datetime = field(default_factory=datetime.now)
    terminationDateTime: Optional[datetime] = None
    localSyncTime: datetime = field(default_factory=datetime.now)
    isTemp: bool = False
    toUpdate: bool = False
    applicationId: int = 0
    type: Optional["Concept"] = None
    ofConcept: Optional["Concept"] = None
    toConcept: Optional["Concept"] = None

    def __post_init__(self):
        """Set ghostId to match id initially."""
        self.ghostId = self.id

    def __repr__(self) -> str:
        return (
            f"Connection(id={self.id}, ofTheConceptId={self.ofTheConceptId}, "
            f"toTheConceptId={self.toTheConceptId}, typeId={self.typeId})"
        )


def create_default_connection() -> Connection:
    """
    Create a default/empty connection with zero values.

    Used as a placeholder when no connection is found.

    Returns:
        A Connection with id=0 indicating "not found".
    """
    return Connection(
        id=0,
        ofTheConceptId=0,
        toTheConceptId=0,
        userId=0,
        typeId=0,
        orderId=0,
        accessId=0
    )
