"""
FreeschemaQuery - Flexible schema-free query construction for CCS.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional, TYPE_CHECKING

from ccs.constants.format_constants import NORMAL
from ccs.models.search.filter_search import FilterSearch

if TYPE_CHECKING:
    from ccs.models.concept import Concept


@dataclass
class FreeschemaQuery:
    """
    Represents a flexible, schema-free query for the CCS system.

    FreeschemaQuery allows complex data retrieval from the concept-based database
    with support for filtering, pagination, nested queries, and multiple output formats.

    Attributes:
        type: Entity type to query (e.g., "the_person", "the_document")
        inpage: Results per page (page size), default 10
        page: Page number (1-indexed), default 1
        concepts: Array of Concept objects to include in query
        conceptIds: Array of concept IDs to query
        selectors: Field selectors for results
        freeschemaQueries: Nested queries for hierarchical searches
        filters: Filter criteria for narrowing results
        filterLogic: Logic for combining filters ("AND" or "OR")
        typeConnection: Connection type for relationships
        order: Sort order ("ASC" or "DESC"), default "DESC"
        outputFormat: Output format constant (NORMAL, DATAID, JUSTDATA, etc.)
        name: Query name/identifier
        reverse: Reverse query direction flag
        limit: Apply strict page size limit
        filterAncestor: Filter for ancestor nodes
        includeInFilter: Include in parent filter operations
        isOldConnectionType: Legacy connection type behavior

    Example:
        >>> # Simple query for persons
        >>> query = FreeschemaQuery(
        ...     type="the_person",
        ...     inpage=20,
        ...     page=1,
        ...     order="ASC"
        ... )

        >>> # Query with filters
        >>> query = FreeschemaQuery(
        ...     type="the_document",
        ...     filters=[
        ...         FilterSearch(type="characterValue", search="Report", logicoperator="LIKE")
        ...     ],
        ...     filterLogic="AND"
        ... )

        >>> # Nested query for hierarchical data
        >>> parent_query = FreeschemaQuery(
        ...     type="the_project",
        ...     freeschemaQueries=[
        ...         FreeschemaQuery(type="the_task", typeConnection="the_project_tasks")
        ...     ]
        ... )
    """
    type: str = ""
    inpage: int = 10
    page: int = 1
    concepts: List[Any] = field(default_factory=list)  # List[Concept]
    conceptIds: List[int] = field(default_factory=list)
    selectors: List[str] = field(default_factory=list)
    freeschemaQueries: List["FreeschemaQuery"] = field(default_factory=list)
    filters: List[FilterSearch] = field(default_factory=list)
    filterLogic: str = ""
    typeConnection: str = ""
    order: str = "DESC"
    outputFormat: int = NORMAL
    name: str = ""
    reverse: bool = False
    limit: bool = False
    filterAncestor: str = ""
    includeInFilter: bool = False
    isOldConnectionType: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "type": self.type,
            "inpage": self.inpage,
            "page": self.page,
            "conceptIds": self.conceptIds,
            "selectors": self.selectors,
            "filterLogic": self.filterLogic,
            "typeConnection": self.typeConnection,
            "order": self.order,
            "outputFormat": self.outputFormat,
            "name": self.name,
            "reverse": self.reverse,
            "limit": self.limit,
            "filterAncestor": self.filterAncestor,
            "includeInFilter": self.includeInFilter,
            "isOldConnectionType": self.isOldConnectionType,
        }

        # Convert concepts if they have to_dict method
        if self.concepts:
            result["concepts"] = [
                c.to_dict() if hasattr(c, "to_dict") else c
                for c in self.concepts
            ]
        else:
            result["concepts"] = []

        # Convert nested queries
        if self.freeschemaQueries:
            result["freeschemaQueries"] = [
                q.to_dict() for q in self.freeschemaQueries
            ]
        else:
            result["freeschemaQueries"] = []

        # Convert filters
        if self.filters:
            result["filters"] = [f.to_dict() for f in self.filters]
        else:
            result["filters"] = []

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FreeschemaQuery":
        """Create FreeschemaQuery from dictionary."""
        # Handle nested freeschemaQueries
        nested_queries = [
            cls.from_dict(q) for q in data.get("freeschemaQueries", [])
        ]

        # Handle filters
        filters = [
            FilterSearch.from_dict(f) for f in data.get("filters", [])
        ]

        return cls(
            type=data.get("type", ""),
            inpage=data.get("inpage", 10),
            page=data.get("page", 1),
            concepts=data.get("concepts", []),
            conceptIds=data.get("conceptIds", []),
            selectors=data.get("selectors", []),
            freeschemaQueries=nested_queries,
            filters=filters,
            filterLogic=data.get("filterLogic", ""),
            typeConnection=data.get("typeConnection", ""),
            order=data.get("order", "DESC"),
            outputFormat=data.get("outputFormat", NORMAL),
            name=data.get("name", ""),
            reverse=data.get("reverse", False),
            limit=data.get("limit", False),
            filterAncestor=data.get("filterAncestor", ""),
            includeInFilter=data.get("includeInFilter", False),
            isOldConnectionType=data.get("isOldConnectionType", False),
        )

    def add_filter(
        self,
        field: str,
        value: str,
        operator: str = "=",
        operateon: str = ""
    ) -> "FreeschemaQuery":
        """
        Add a filter to the query (fluent interface).

        Args:
            field: Field name to filter on
            value: Value to filter by
            operator: Comparison operator (default "=")
            operateon: Operand type (value, text, date, id)

        Returns:
            Self for method chaining

        Example:
            >>> query = FreeschemaQuery(type="the_person")
            >>> query.add_filter("characterValue", "John").add_filter("userId", "101", operateon="id")
        """
        self.filters.append(FilterSearch(
            type=field,
            search=value,
            logicoperator=operator,
            index=len(self.filters),
            operateon=operateon,
        ))
        return self

    def add_nested_query(
        self,
        query: "FreeschemaQuery"
    ) -> "FreeschemaQuery":
        """
        Add a nested query for hierarchical searches (fluent interface).

        Args:
            query: The nested FreeschemaQuery

        Returns:
            Self for method chaining
        """
        self.freeschemaQueries.append(query)
        return self
