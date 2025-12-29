"""
Local sync data - manages the queue of concepts/connections pending backend sync.

Tracks all locally created items that need to be synchronized with the backend
server when connectivity is available. Supports transactions for atomic operations.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from ccs.models.concept import Concept, create_default_concept
from ccs.models.connection import Connection


@dataclass
class SyncContainer:
    """Container for transaction data."""
    id: str
    data: "InnerActions"
    createdDate: str


@dataclass
class InnerActions:
    """Tracks concepts and connections created during an operation."""
    concepts: List[Concept] = field(default_factory=list)
    connections: List[Connection] = field(default_factory=list)

    def clear(self) -> None:
        """Clear all tracked actions."""
        self.concepts.clear()
        self.connections.clear()


class LocalSyncData:
    """
    Manages the sync queue for offline-first operations with transaction support.

    Concepts and connections created locally are added to this queue.
    When online, SyncDataOnline() sends them to the backend.

    **Transaction Support:**
    - initializeTransaction(): Start a new transaction
    - markTransactionActions(): Track actions within a transaction
    - commitTransaction(): Sync and finalize a transaction
    - rollbackTransaction(): Cancel a transaction

    Example:
        >>> LocalSyncData.AddConcept(new_concept)
        >>> pending = LocalSyncData.GetPendingConcepts()
        >>> await LocalSyncData.SyncDataOnline()

    Example with transaction:
        >>> await LocalSyncData.initializeTransaction("tx-123")
        >>> # ... create concepts/connections ...
        >>> await LocalSyncData.SyncDataOnline("tx-123")
    """

    # Queue of concepts pending sync
    conceptsSyncArray: List[Concept] = []

    # Queue of connections pending sync
    connectionSyncArray: List[Connection] = []

    # Map of ghost IDs to real IDs after sync
    ghostIdMap: Dict[int, int] = {}

    # Transaction collections
    transactionCollections: List[SyncContainer] = []

    # ============================================================
    # Concept Management
    # ============================================================

    @classmethod
    def CheckContains(cls, concept: Concept) -> bool:
        """Check if a concept is already in the sync array."""
        for c in cls.conceptsSyncArray:
            if c.id == concept.id:
                return True
        return False

    @classmethod
    def CheckIfTheConceptIdExists(cls, id: int, conceptList: List[Concept]) -> Concept:
        """Check if a concept with the given ID exists in the list."""
        for concept in conceptList:
            if id == concept.ghostId or id == concept.id:
                return concept
        return create_default_concept()

    @classmethod
    def AddConcept(cls, concept: Concept) -> None:
        """
        Add a concept to the sync queue.

        Args:
            concept: The Concept to queue for sync.
        """
        if concept.id == 0:
            return

        existingConcept = cls.CheckIfTheConceptIdExists(concept.id, cls.conceptsSyncArray)
        if existingConcept.id == 0:
            cls.conceptsSyncArray.append(concept)

    @classmethod
    def RemoveConcept(cls, concept: Concept) -> None:
        """
        Remove a concept from the sync queue.

        Args:
            concept: The Concept to remove from queue.
        """
        cls.conceptsSyncArray = [
            c for c in cls.conceptsSyncArray if c.id != concept.id
        ]

    @classmethod
    def SyncDataDelete(cls, id: int) -> None:
        """Remove concept and related connections from sync arrays."""
        cls.conceptsSyncArray = [c for c in cls.conceptsSyncArray if c.id != id]
        cls.connectionSyncArray = [
            conn for conn in cls.connectionSyncArray
            if conn.ofTheConceptId != id and conn.toTheConceptId != id and conn.typeId != id
        ]

    # ============================================================
    # Connection Management
    # ============================================================

    @classmethod
    def CheckContainsConnection(cls, connection: Connection) -> bool:
        """Check if a connection is already in the sync array."""
        for conn in cls.connectionSyncArray:
            if conn.id == connection.id:
                return True
        return False

    @classmethod
    def AddConnection(cls, connection: Connection) -> None:
        """
        Add a connection to the sync queue.

        Args:
            connection: The Connection to queue for sync.
        """
        if not cls.CheckContainsConnection(connection):
            cls.connectionSyncArray.append(connection)

    @classmethod
    def RemoveConnection(cls, connection: Connection) -> None:
        """
        Remove a connection from the sync queue.

        Args:
            connection: The Connection to remove from queue.
        """
        cls.connectionSyncArray = [
            c for c in cls.connectionSyncArray if c.id != connection.id
        ]

    @classmethod
    def RemoveConnectionById(cls, connectionId: int) -> None:
        """Remove a connection by ID from the sync queue."""
        cls.connectionSyncArray = [
            c for c in cls.connectionSyncArray if c.id != connectionId
        ]

    # ============================================================
    # Query Methods
    # ============================================================

    @classmethod
    def GetPendingConcepts(cls) -> List[Concept]:
        """Get all concepts pending sync."""
        return cls.conceptsSyncArray.copy()

    @classmethod
    def GetPendingConnections(cls) -> List[Connection]:
        """Get all connections pending sync."""
        return cls.connectionSyncArray.copy()

    @classmethod
    def ClearPendingConcepts(cls) -> None:
        """Clear the pending concepts queue."""
        cls.conceptsSyncArray.clear()

    @classmethod
    def ClearPendingConnections(cls) -> None:
        """Clear the pending connections queue."""
        cls.connectionSyncArray.clear()

    @classmethod
    def GetPendingCount(cls) -> int:
        """Get the total count of items pending sync."""
        return len(cls.conceptsSyncArray) + len(cls.connectionSyncArray)

    # ============================================================
    # Transaction Management
    # ============================================================

    @classmethod
    async def initializeTransaction(cls, transactionId: str) -> None:
        """
        Initialize a new transaction.

        Args:
            transactionId: Unique identifier for the transaction.
        """
        # Check if transaction already exists
        if any(item.id == transactionId for item in cls.transactionCollections):
            return

        cls.transactionCollections.append(SyncContainer(
            id=transactionId,
            data=InnerActions(),
            createdDate=datetime.now().isoformat()
        ))

    @classmethod
    async def markTransactionActions(cls, transactionId: str, actions: InnerActions) -> None:
        """
        Mark actions as belonging to a transaction.

        Args:
            transactionId: The transaction identifier.
            actions: The actions to mark.
        """
        import copy

        # Update transaction with actions
        for i, tran in enumerate(cls.transactionCollections):
            if tran.id == transactionId:
                cls.transactionCollections[i] = SyncContainer(
                    id=tran.id,
                    data=InnerActions(
                        concepts=copy.deepcopy(actions.concepts),
                        connections=copy.deepcopy(actions.connections)
                    ),
                    createdDate=tran.createdDate
                )
                break

        # Remove marked concepts/connections from main sync arrays
        actionConceptIds = {c.id for c in actions.concepts} | {c.ghostId for c in actions.concepts}
        actionConnectionIds = {c.id for c in actions.connections} | {c.ghostId for c in actions.connections}

        cls.conceptsSyncArray = [
            c for c in cls.conceptsSyncArray
            if c.id not in actionConceptIds and c.ghostId not in actionConceptIds
        ]
        cls.connectionSyncArray = [
            c for c in cls.connectionSyncArray
            if c.id not in actionConnectionIds and c.ghostId not in actionConnectionIds
        ]

    @classmethod
    async def rollbackTransaction(cls, transactionId: str, actions: InnerActions) -> None:
        """
        Rollback a transaction, discarding all its actions.

        Args:
            transactionId: The transaction to rollback.
            actions: The actions that were part of the transaction.
        """
        cls.transactionCollections = [
            tran for tran in cls.transactionCollections
            if tran.id != transactionId
        ]

    # ============================================================
    # Sync Operations
    # ============================================================

    @classmethod
    async def SyncDataOnline(
        cls,
        transactionId: Optional[str] = None,
        actions: Optional[InnerActions] = None,
        withAuth: bool = True
    ) -> List[Concept]:
        """
        Sync all pending data to the backend.

        This method sends all pending concepts and connections to the backend API.
        It can work with a specific transaction or sync all pending items.

        Args:
            transactionId: Optional transaction ID to sync specific transaction.
            actions: Optional InnerActions to sync specific items.
            withAuth: Whether to include authentication (default: True).

        Returns:
            List of synced concepts.

        Example:
            >>> # Sync all pending
            >>> await LocalSyncData.SyncDataOnline()

            >>> # Sync specific transaction
            >>> await LocalSyncData.SyncDataOnline(transactionId="tx-123")
        """
        conceptsArray: List[Concept] = []
        connectionsArray: List[Connection] = []

        # Determine which data to sync
        if transactionId:
            # Find and use transaction data
            transaction = next(
                (t for t in cls.transactionCollections if t.id == transactionId),
                None
            )
            if transaction:
                # Remove transaction from list
                cls.transactionCollections = [
                    t for t in cls.transactionCollections if t.id != transactionId
                ]
                # Clean old transactions (older than 7 days)
                cutoffDate = datetime.now() - timedelta(days=7)
                cls.transactionCollections = [
                    t for t in cls.transactionCollections
                    if datetime.fromisoformat(t.createdDate) > cutoffDate
                ]

                conceptsArray = transaction.data.concepts.copy()
                connectionsArray = transaction.data.connections.copy()
            else:
                return []

        elif actions and actions.concepts and actions.connections is not None:
            # Use provided actions
            conceptsArray = actions.concepts.copy()
            connectionsArray = actions.connections.copy()

            # Remove from main sync arrays
            actionIds = {c.id for c in actions.concepts} | {c.ghostId for c in actions.concepts}
            cls.conceptsSyncArray = [
                c for c in cls.conceptsSyncArray
                if c.id not in actionIds and c.ghostId not in actionIds
            ]

        else:
            # Sync all pending
            conceptsArray = cls.conceptsSyncArray.copy()
            connectionsArray = cls.connectionSyncArray.copy()
            cls.conceptsSyncArray = []
            cls.connectionSyncArray = []

        # Mark concepts as being synced
        from ccs.data.local_concept_data import LocalConceptsData
        for concept in conceptsArray:
            LocalConceptsData.UpdateConceptSyncStatus(concept.id)

        # Call the API to sync
        try:
            result = await cls._callSyncApi(conceptsArray, connectionsArray, withAuth)
            return result.get("concepts", conceptsArray)
        except Exception as error:
            print(f"Error syncing data: {error}")
            raise error

    @classmethod
    async def SyncDataOnlineWithoutAuth(
        cls,
        transactionId: Optional[str] = None,
        actions: Optional[InnerActions] = None
    ) -> List[Concept]:
        """Sync data without authentication."""
        return await cls.SyncDataOnline(transactionId, actions, withAuth=False)

    @classmethod
    async def _callSyncApi(
        cls,
        concepts: List[Concept],
        connections: List[Connection],
        withAuth: bool = True
    ) -> Dict[str, Any]:
        """
        Call the backend API to sync concepts and connections.

        This is the actual HTTP call to the ghost concept API.
        Automatically retries with fresh token on 401 Unauthorized.

        Args:
            concepts: List of concepts to sync.
            connections: List of connections to sync.
            withAuth: Whether to include authentication.

        Returns:
            Dictionary with synced concepts and connections.
        """
        import aiohttp
        from ccs.config.base_url import BaseUrl
        from ccs.api.http_client import post_with_retry, TokenRefreshError

        url = BaseUrl.CreateGhostConceptApiUrl(withAuth)

        # Prepare request data
        conceptsData = []
        for c in concepts:
            conceptsData.append({
                "id": c.id,
                "ghostId": c.ghostId,
                "userId": c.userId,
                "typeId": c.typeId,
                "categoryId": c.categoryId,
                "referentId": c.referentId,
                "characterValue": c.characterValue,
                "accessId": c.accessId,
                "typeCharacter": c.typeCharacter,
                "isComposition": c.isComposition,
            })

        connectionsData = []
        for conn in connections:
            connectionsData.append({
                "id": conn.id,
                "ghostId": conn.ghostId,
                "ofTheConceptId": conn.ofTheConceptId,
                "toTheConceptId": conn.toTheConceptId,
                "userId": conn.userId,
                "typeId": conn.typeId,
                "orderId": conn.orderId,
                "accessId": conn.accessId,
                "typeCharacter": conn.typeCharacter,
            })

        payload = {
            "concepts": conceptsData,
            "connections": connectionsData
        }

        headers = {"Content-Type": "application/json"}

        try:
            # Use post_with_retry for automatic token refresh on 401
            if withAuth:
                response = await post_with_retry(url, headers=headers, json=payload)
            else:
                # Without auth, use regular aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers) as response:
                        if response.status != 200:
                            raise Exception(f"Sync failed with status {response.status}")
                        result = await response.json()

                        # Update ghost ID map with server-assigned IDs
                        if "concepts" in result:
                            for serverConcept in result["concepts"]:
                                if serverConcept.get("ghostId") and serverConcept.get("id"):
                                    cls.ghostIdMap[serverConcept["ghostId"]] = serverConcept["id"]

                        return result

            # Handle authenticated response (from post_with_retry)
            if response.status != 200:
                raise Exception(f"Sync failed with status {response.status}")

            result = await response.json()

            # Update ghost ID map with server-assigned IDs
            if "concepts" in result:
                for serverConcept in result["concepts"]:
                    if serverConcept.get("ghostId") and serverConcept.get("id"):
                        cls.ghostIdMap[serverConcept["ghostId"]] = serverConcept["id"]

            return result

        except TokenRefreshError as e:
            print(f"Authentication error during sync: {e}")
            # Return original data if auth fails
            return {"concepts": concepts, "connections": connections, "error": str(e)}
        except aiohttp.ClientError as e:
            print(f"HTTP error during sync: {e}")
            # Return original data if sync fails
            return {"concepts": concepts, "connections": connections, "error": str(e)}
