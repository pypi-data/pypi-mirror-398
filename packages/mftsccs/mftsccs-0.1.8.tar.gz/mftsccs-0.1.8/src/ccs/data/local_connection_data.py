"""
Local connection data storage - manages connections in local memory.

Provides storage and retrieval for locally created connections.
"""

from typing import List, Optional, Dict
from ccs.models.connection import Connection, create_default_connection


class LocalConnectionData:
    """
    Manages local connection storage with indexing.

    Stores connections in memory for fast access and provides
    methods for adding, removing, and querying connections.

    Example:
        >>> LocalConnectionData.AddConnection(my_connection)
        >>> found = LocalConnectionData.GetConnection(connection_id)
        >>> connections = LocalConnectionData.GetConnectionsOfCompositionLocal(comp_id)
    """

    # Primary storage - list of connections
    connectionArray: List[Connection] = []

    # Dictionary for fast lookup by ID
    connectionDictionary: Dict[int, Connection] = {}

    @classmethod
    def CheckContains(cls, connection: Connection) -> bool:
        """Check if a connection is already in the array."""
        for conn in cls.connectionArray:
            if conn.id == connection.id:
                return True
        return False

    @classmethod
    def AddConnection(cls, connection: Connection) -> None:
        """
        Add a connection to local storage.

        If connection already exists, it will be replaced.

        Args:
            connection: The Connection to store.
        """
        contains = cls.CheckContains(connection)
        if contains:
            cls.RemoveConnection(connection)

        cls.connectionArray.append(connection)
        cls.connectionDictionary[connection.id] = connection

    @classmethod
    def AddConnectionToMemory(cls, connection: Connection) -> None:
        """Add a connection to memory only (no persistence)."""
        contains = cls.CheckContains(connection)
        if contains:
            cls.RemoveConnection(connection)
        cls.connectionArray.append(connection)

    @classmethod
    def AddToDictionary(cls, connection: Connection) -> None:
        """Add connection to the dictionary for fast lookup."""
        cls.connectionDictionary[connection.id] = connection

    @classmethod
    def RemoveConnection(cls, connection: Connection) -> None:
        """
        Remove a connection from storage.

        Args:
            connection: The Connection to remove.
        """
        cls.connectionArray = [
            c for c in cls.connectionArray if c.id != connection.id
        ]
        cls.connectionDictionary.pop(connection.id, None)

    @classmethod
    def RemoveConnectionById(cls, connectionId: int) -> None:
        """
        Remove a connection by its ID.

        Args:
            connectionId: The ID of the connection to remove.
        """
        cls.connectionArray = [
            c for c in cls.connectionArray if c.id != connectionId
        ]
        cls.connectionDictionary.pop(connectionId, None)

        # Also remove from sync data
        from ccs.data.local_sync_data import LocalSyncData
        LocalSyncData.RemoveConnectionById(connectionId)

    @classmethod
    def GetConnection(cls, id: int) -> Optional[Connection]:
        """
        Get a connection by its ID.

        Args:
            id: The ID of the connection to retrieve.

        Returns:
            The Connection if found, or None.
        """
        # Try dictionary first for O(1) lookup
        if id in cls.connectionDictionary:
            return cls.connectionDictionary[id]

        # Fall back to array search
        for conn in cls.connectionArray:
            if conn.id == id:
                return conn
        return None

    @classmethod
    def GetConnectionsOfCompositionLocal(cls, id: int) -> List[Connection]:
        """
        Get all connections belonging to a composition.

        Args:
            id: The composition (type) ID to filter by.

        Returns:
            List of connections with the given typeId.
        """
        return [
            conn for conn in cls.connectionArray
            if conn.typeId == id
        ]

    @classmethod
    def GetConnectionOfCompositionAndTypeLocal(
        cls,
        typeId: int,
        ofTheConceptId: int
    ) -> List[Connection]:
        """
        Get connections by type and source concept.

        Args:
            typeId: The type ID to filter by.
            ofTheConceptId: The source concept ID to filter by.

        Returns:
            List of matching connections.
        """
        return [
            conn for conn in cls.connectionArray
            if conn.typeId == typeId and conn.ofTheConceptId == ofTheConceptId
        ]

    @classmethod
    def GetConnectionsByOfTheConcept(cls, ofTheConceptId: int) -> List[Connection]:
        """
        Get all connections from a specific concept.

        Args:
            ofTheConceptId: The source concept ID.

        Returns:
            List of connections originating from this concept.
        """
        return [
            conn for conn in cls.connectionArray
            if conn.ofTheConceptId == ofTheConceptId
        ]

    @classmethod
    def GetConnectionsByToTheConcept(cls, toTheConceptId: int) -> List[Connection]:
        """
        Get all connections pointing to a specific concept.

        Args:
            toTheConceptId: The target concept ID.

        Returns:
            List of connections pointing to this concept.
        """
        return [
            conn for conn in cls.connectionArray
            if conn.toTheConceptId == toTheConceptId
        ]

    @classmethod
    def AddPermanentConnection(cls, connection: Connection) -> None:
        """
        Add a permanently synced connection (positive ID from server).

        Args:
            connection: The synced Connection with server ID.
        """
        if connection.id > 0:
            # Remove local version if exists
            if connection.ghostId and connection.ghostId != connection.id:
                cls.RemoveConnectionById(connection.ghostId)
            cls.AddConnection(connection)

    @classmethod
    def ClearData(cls) -> None:
        """Clear all stored connections."""
        cls.connectionArray.clear()
        cls.connectionDictionary.clear()
