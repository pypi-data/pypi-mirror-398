"""
FilterSearch - Filter criteria for FreeSchema queries.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FilterSearch:
    """
    Represents a filter criterion for FreeSchema queries.

    Filters allow you to narrow down query results based on specific field values
    and comparison operators.

    Attributes:
        type: Field name to filter on (e.g., "characterValue", "userId")
        search: Value to filter by
        logicoperator: Comparison operator (=, !=, >, <, >=, <=, LIKE, IN)
        index: Position in filter array (for ordering)
        composition: Whether filter applies to compositions
        name: Filter identifier/name
        operateon: Operand type (value, text, date, id)

    Example:
        >>> # Filter by exact match
        >>> filter1 = FilterSearch(type="characterValue", search="John", logicoperator="=")

        >>> # Filter with LIKE operator
        >>> filter2 = FilterSearch(type="characterValue", search="%Smith%", logicoperator="LIKE")

        >>> # Filter by user ID
        >>> filter3 = FilterSearch(type="userId", search="101", logicoperator="=", operateon="id")
    """
    type: str = ""
    search: str = ""
    logicoperator: str = "="
    index: int = 0
    composition: bool = True
    name: str = ""
    operateon: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "search": self.search,
            "logicoperator": self.logicoperator,
            "index": self.index,
            "composition": self.composition,
            "name": self.name,
            "operateon": self.operateon,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FilterSearch":
        """Create FilterSearch from dictionary."""
        return cls(
            type=data.get("type", ""),
            search=data.get("search", ""),
            logicoperator=data.get("logicoperator", "="),
            index=data.get("index", 0),
            composition=data.get("composition", True),
            name=data.get("name", ""),
            operateon=data.get("operateon", ""),
        )
