"""
Connection ordering utilities.
"""

from typing import List
from ccs.models.connection import Connection


def order_connections(connections: List[Connection], order: str = "DESC") -> List[Connection]:
    """
    Order connections by ID in ascending or descending order.

    Args:
        connections: List of Connection objects to sort
        order: Sort order - "ASC" for ascending, "DESC" for descending (default)

    Returns:
        Sorted list of connections

    Example:
        >>> connections = [conn1, conn2, conn3]
        >>> sorted_conns = order_connections(connections, "ASC")
    """
    if order.upper() == "ASC":
        return sorted(connections, key=lambda c: c.id)
    else:
        return sorted(connections, key=lambda c: c.id, reverse=True)
