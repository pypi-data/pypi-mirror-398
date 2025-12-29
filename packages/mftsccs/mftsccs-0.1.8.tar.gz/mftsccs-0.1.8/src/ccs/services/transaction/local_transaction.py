"""
LocalTransaction - Transaction support for batching local operations.

Allows grouping multiple concept/connection operations into a single
transaction that can be committed (synced) or rolled back atomically.
"""

import random
from typing import Optional

from ccs.models.concept import Concept
from ccs.models.connection import Connection
from ccs.data.local_sync_data import LocalSyncData, InnerActions
from ccs.services.local.make_the_instance_concept_local import MakeTheInstanceConceptLocal
from ccs.services.local.make_the_type_local import MakeTheTypeConceptLocal
from ccs.services.local.create_the_concept_local import CreateTheConceptLocal
from ccs.services.local.create_the_connection_local import (
    CreateTheConnectionLocal,
    CreateConnection as CreateConnectionFunc,
    CreateConnectionBetweenTwoConceptsLocal,
)


class LocalTransaction:
    """
    Transaction support for batching local concept/connection operations.

    LocalTransaction allows you to group multiple operations together and
    sync them to the backend in a single batch. This is useful for:

    - Creating complex data structures atomically
    - Ensuring all related concepts/connections are synced together
    - Rolling back if an error occurs during creation

    **Lifecycle:**
    1. Create transaction: `tx = LocalTransaction()`
    2. Initialize: `await tx.initialize()`
    3. Perform operations: `await tx.MakeTheInstanceConceptLocal(...)`
    4. Commit (sync): `await tx.commitTransaction()`
    5. Or rollback: `await tx.rollbackTransaction()`

    Example:
        >>> tx = LocalTransaction()
        >>> await tx.initialize()
        >>>
        >>> try:
        ...     # Create concepts within transaction
        ...     person = await tx.MakeTheInstanceConceptLocal(
        ...         type="the_person",
        ...         referent="",
        ...         composition=True,
        ...         userId=101
        ...     )
        ...     name = await tx.MakeTheInstanceConceptLocal(
        ...         type="the_name",
        ...         referent="Alice",
        ...         userId=101
        ...     )
        ...     # Commit syncs everything to backend
        ...     await tx.commitTransaction()
        ... except Exception as e:
        ...     # Rollback discards all changes
        ...     await tx.rollbackTransaction()
        ...     raise e
    """

    def __init__(self):
        """Initialize a new transaction."""
        self.transactionId: str = str(random.random())[5:]
        self.actions: InnerActions = InnerActions()
        self.success: bool = True

    async def initialize(self) -> None:
        """
        Initialize the transaction.

        Must be called before performing any operations.
        """
        await LocalSyncData.initializeTransaction(self.transactionId)

    async def commitTransaction(self) -> None:
        """
        Commit the transaction - sync all created data to the backend.

        Raises:
            Exception: If the transaction has already been committed or rolled back.
        """
        if not self.success:
            raise Exception("Query Transaction Expired")

        output = await LocalSyncData.SyncDataOnline(self.transactionId)
        self.actions = InnerActions()
        self.success = False
        return output

    async def commitTransactionWithoutAuth(self) -> None:
        """
        Commit the transaction without authentication.

        Useful for public/anonymous operations.
        """
        if not self.success:
            raise Exception("Query Transaction Expired")

        output = await LocalSyncData.SyncDataOnlineWithoutAuth(self.transactionId)
        self.actions = InnerActions()
        self.success = False
        return output

    async def rollbackTransaction(self) -> None:
        """
        Rollback the transaction - discard all created data.

        Call this if an error occurs and you want to cancel all operations.
        """
        self.success = False
        await LocalSyncData.rollbackTransaction(self.transactionId, self.actions)
        self.actions = InnerActions()

    async def _markAction(self) -> None:
        """Mark current actions as belonging to this transaction."""
        await LocalSyncData.markTransactionActions(self.transactionId, self.actions)

    # ============================================================
    # Concept Operations
    # ============================================================

    async def MakeTheInstanceConceptLocal(
        self,
        type: str,
        referent: str,
        composition: bool = False,
        userId: int = 0,
        accessId: int = 4,
        sessionInformationId: int = 999,
        referentId: int = 0
    ) -> Concept:
        """
        Create or retrieve an instance concept within this transaction.

        Args:
            type: The type/key of the concept (e.g., "the_name", "the_status").
            referent: The actual value/content of the concept.
            composition: True to always create new (unique instances).
            userId: The ID of the user creating this concept.
            accessId: Access control level.
            sessionInformationId: Session identifier.
            referentId: Optional reference to another concept.

        Returns:
            The created or retrieved Concept.

        Raises:
            Exception: If the transaction has expired.

        Example:
            >>> concept = await tx.MakeTheInstanceConceptLocal(
            ...     type="the_email",
            ...     referent="alice@example.com",
            ...     userId=101
            ... )
        """
        if not self.success:
            raise Exception("Query Transaction Expired")

        try:
            concept = await MakeTheInstanceConceptLocal(
                type=type,
                referent=referent,
                composition=composition,
                userId=userId,
                accessId=accessId,
                sessionInformationId=sessionInformationId,
                referentId=referentId,
                actions=self.actions
            )
            await self._markAction()
            return concept

        except Exception as err:
            print(f"Transaction error: {err}")
            self.success = False
            raise err

    async def MakeTheTypeConceptLocal(
        self,
        typeString: str,
        sessionId: int = 999,
        sessionUserId: int = 999,
        userId: int = 0
    ) -> Concept:
        """
        Create or retrieve a type concept within this transaction.

        Args:
            typeString: The type name (e.g., "the_status", "the_person_email").
            sessionId: Session identifier.
            sessionUserId: Session user ID.
            userId: User creating the type.

        Returns:
            The type Concept.
        """
        if not self.success:
            raise Exception("Query Transaction Expired")

        try:
            concept = await MakeTheTypeConceptLocal(
                typeString=typeString,
                sessionId=sessionId,
                sessionUserId=sessionUserId,
                userId=userId,
                actions=self.actions
            )
            await self._markAction()
            return concept

        except Exception as err:
            print(f"Transaction error: {err}")
            self.success = False
            raise err

    async def CreateTheConceptLocal(
        self,
        referent: str,
        typecharacter: str,
        userId: int,
        categoryId: int,
        typeId: int,
        accessId: int,
        isComposition: bool = False,
        referentId: Optional[int] = 0
    ) -> Concept:
        """
        Create a concept directly within this transaction.

        This is a lower-level function - prefer MakeTheInstanceConceptLocal
        for most use cases.

        Args:
            referent: The character value of the concept.
            typecharacter: The type name string.
            userId: User ID.
            categoryId: Category ID.
            typeId: Type ID.
            accessId: Access control level.
            isComposition: Whether this is a composition.
            referentId: Reference to another concept.

        Returns:
            The created Concept.
        """
        if not self.success:
            raise Exception("Query Transaction Expired")

        try:
            concept = await CreateTheConceptLocal(
                referent=referent,
                typecharacter=typecharacter,
                userId=userId,
                categoryId=categoryId,
                typeId=typeId,
                accessId=accessId,
                isComposition=isComposition,
                referentId=referentId,
                actions=self.actions
            )
            await self._markAction()
            return concept

        except Exception as err:
            print(f"Transaction error: {err}")
            self.success = False
            raise err

    # ============================================================
    # Connection Operations
    # ============================================================

    async def CreateTheConnectionLocal(
        self,
        ofTheConceptId: int,
        toTheConceptId: int,
        typeId: int,
        orderId: int = 1,
        typeString: str = "",
        userId: int = 999
    ) -> Connection:
        """
        Create a connection within this transaction.

        Args:
            ofTheConceptId: Source concept ID (FROM).
            toTheConceptId: Target concept ID (TO).
            typeId: The type classification for this connection.
            orderId: Order identifier for sorting. Default: 1.
            typeString: Human-readable type name. Default: "".
            userId: The ID of the user creating this connection. Default: 999.

        Returns:
            The created Connection object.

        Raises:
            Exception: If the transaction has expired.

        Example:
            >>> conn = await tx.CreateTheConnectionLocal(
            ...     ofTheConceptId=-12345,
            ...     toTheConceptId=-67890,
            ...     typeId=-11111,
            ...     orderId=1,
            ...     userId=101
            ... )
        """
        if not self.success:
            raise Exception("Query Transaction Expired")

        try:
            connection = await CreateTheConnectionLocal(
                ofTheConceptId=ofTheConceptId,
                toTheConceptId=toTheConceptId,
                typeId=typeId,
                orderId=orderId,
                typeString=typeString,
                userId=userId,
                actions=self.actions
            )
            await self._markAction()
            return connection

        except Exception as err:
            print(f"Transaction error: {err}")
            self.success = False
            raise err

    async def CreateConnection(
        self,
        ofTheConcept: Concept,
        toTheConcept: Concept,
        connectionTypeString: str
    ) -> Connection:
        """
        Simplified connection creator that accepts concepts and a type string.

        This is a convenience wrapper that:
        1. Accepts Concept objects instead of IDs
        2. Creates the connection type concept if it doesn't exist
        3. Sets appropriate defaults for external connections (orderId=1000)

        Args:
            ofTheConcept: The source Concept object (FROM).
            toTheConcept: The target Concept object (TO).
            connectionTypeString: Type name as string (e.g., "the_person_email").

        Returns:
            The created Connection object.

        Example:
            >>> person = await tx.MakeTheInstanceConceptLocal("the_person", "", True, 101)
            >>> email = await tx.MakeTheInstanceConceptLocal("the_email", "alice@example.com", False, 101)
            >>> connection = await tx.CreateConnection(person, email, "the_person_email")
        """
        if not self.success:
            raise Exception("Query Transaction Expired")

        try:
            connection = await CreateConnectionFunc(
                ofTheConcept=ofTheConcept,
                toTheConcept=toTheConcept,
                connectionTypeString=connectionTypeString,
                actions=self.actions
            )
            await self._markAction()
            return connection

        except Exception as err:
            print(f"Transaction error: {err}")
            self.success = False
            raise err

    async def CreateConnectionBetweenTwoConceptsLocal(
        self,
        ofTheConcept: Concept,
        toTheConcept: Concept,
        linker: str,
        both: bool = False
    ) -> Connection:
        """
        Creates a named connection between two concepts with optional bidirectional linking.

        Args:
            ofTheConcept: Source concept (connection starts here).
            toTheConcept: Target concept (connection points here).
            linker: Relationship name (e.g., "knows", "works_at", "has").
            both: If True, creates bidirectional connection (both A→B and B→A).

        Returns:
            The forward connection object.

        Example:
            >>> # Create unidirectional "Alice knows Bob"
            >>> conn = await tx.CreateConnectionBetweenTwoConceptsLocal(
            ...     aliceConcept,
            ...     bobConcept,
            ...     "knows",
            ...     both=False
            ... )

            >>> # Create bidirectional "Alice friends Bob"
            >>> await tx.CreateConnectionBetweenTwoConceptsLocal(
            ...     aliceConcept,
            ...     bobConcept,
            ...     "friends",
            ...     both=True
            ... )
        """
        if not self.success:
            raise Exception("Query Transaction Expired")

        try:
            connection = await CreateConnectionBetweenTwoConceptsLocal(
                ofTheConcept=ofTheConcept,
                toTheConcept=toTheConcept,
                linker=linker,
                both=both,
                actions=self.actions
            )
            await self._markAction()
            return connection

        except Exception as err:
            print(f"Transaction error: {err}")
            self.success = False
            raise err

    # ============================================================
    # Composition Operations (to be implemented)
    # ============================================================

    # TODO: Add CreateTheCompositionLocal
