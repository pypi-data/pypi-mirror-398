"""
Inner actions - tracks concepts and connections created during operations.

Used for batch operations, rollback, and sync management.
"""

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ccs.models.concept import Concept


@dataclass
class InnerActions:
    """
    Tracks all concepts and connections created during an operation.

    Used to:
    - Track what was created for potential rollback
    - Batch items for sync operations
    - Provide visibility into operation results

    Example:
        >>> actions = InnerActions()
        >>> # ... perform operations that populate actions.concepts
        >>> print(f"Created {len(actions.concepts)} concepts")
    """

    concepts: List["Concept"] = field(default_factory=list)
    connections: List = field(default_factory=list)  # Connection type added later

    def clear(self) -> None:
        """Clear all tracked actions."""
        self.concepts.clear()
        self.connections.clear()

    def __repr__(self) -> str:
        return (
            f"InnerActions(concepts={len(self.concepts)}, "
            f"connections={len(self.connections)})"
        )
