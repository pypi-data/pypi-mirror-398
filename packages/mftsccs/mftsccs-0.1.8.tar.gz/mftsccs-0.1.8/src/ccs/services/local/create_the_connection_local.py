"""
Create connection locally - creates connections in local storage without backend sync.

This module provides functions for creating offline-first connections between concepts.
"""

from typing import Optional

from ccs.models.concept import Concept
from ccs.models.connection import Connection, create_default_connection
from ccs.data.local_sync_data import LocalSyncData, InnerActions
from ccs.data.local_connection_data import LocalConnectionData
from ccs.data.local_id import LocalId
from ccs.services.local.make_the_type_local import MakeTheTypeConceptLocal
from ccs.services.local.make_the_instance_concept_local import MakeTheInstanceConceptLocal


async def CreateTheConnectionLocal(
    ofTheConceptId: int,
    toTheConceptId: int,
    typeId: int,
    orderId: int = 1,
    typeString: str = "",
    userId: int = 999,
    actions: Optional[InnerActions] = None
) -> Connection:
    """
    Creates a connection in local storage without syncing to the backend.

    This is the primary function for creating offline-first connections. The connection
    is stored locally in memory, but NOT immediately sent to the backend. Sync happens
    later via LocalSyncData.SyncDataOnline().

    **Virtual ID System:**
    - Generates a negative ID (e.g., -67890) to indicate local/virtual status
    - id and ghostId are initially equal and both negative
    - After backend sync: id becomes positive (real backend ID)
    - ghostId remains negative (preserves original local ID)

    **Connection Types:**
    - **Internal Connections**: orderId < 3 (within a composition)
      - typeId is typically the composition ID
    - **External Connections**: orderId >= 999 (between different entities)
      - typeId is a type concept ID
      - typeString provides human-readable type name

    **Self-Connection Prevention:**
    If ofTheConceptId equals toTheConceptId, returns an empty connection (prevents loops).

    Args:
        ofTheConceptId: Source concept ID (FROM). Can be negative (local) or positive (server).
        toTheConceptId: Target concept ID (TO). Can be negative (local) or positive (server).
        typeId: The type classification for this connection.
        orderId: Order identifier for sorting. < 3 = internal, >= 999 = external. Default: 1.
        typeString: Human-readable type name (e.g., "the_person_email"). Default: "".
        userId: The ID of the user creating this connection. Default: 999.
        actions: Action tracking object for batch operations.

    Returns:
        The created Connection object with negative ID.
        Returns empty connection (all IDs = 0) if self-connection attempted.

    Example:
        >>> # Create internal connection (within composition)
        >>> conn = await CreateTheConnectionLocal(
        ...     ofTheConceptId=-12345,
        ...     toTheConceptId=-67890,
        ...     typeId=-11111,
        ...     orderId=1,
        ...     userId=101
        ... )
        >>> print(conn.id)  # -99999 (negative = local)

    Example:
        >>> # Create external connection (between entities)
        >>> conn = await CreateTheConnectionLocal(
        ...     ofTheConceptId=123,
        ...     toTheConceptId=456,
        ...     typeId=789,
        ...     orderId=1000,
        ...     typeString="the_person_email",
        ...     userId=101
        ... )
    """
    if actions is None:
        actions = InnerActions()

    try:
        accessId = 4

        # Generate unique negative ID for local connection
        randomId = LocalId.get_connection_id()

        # Initialize empty connection (for self-connection case)
        connection = create_default_connection()

        # Prevent self-connections
        if ofTheConceptId != toTheConceptId:
            connection = Connection(
                id=randomId,
                ofTheConceptId=ofTheConceptId,
                toTheConceptId=toTheConceptId,
                userId=userId,
                typeId=typeId,
                orderId=orderId,
                accessId=accessId
            )
            connection.isTemp = True
            connection.typeCharacter = typeString

            # Add to sync queue and local storage
            LocalSyncData.AddConnection(connection)
            LocalConnectionData.AddConnection(connection)

            # Track in actions
            actions.connections.append(connection)

        return connection

    except Exception as error:
        print(f"Error in CreateTheConnectionLocal: {error}")
        raise error


async def CreateConnection(
    ofTheConcept: Concept,
    toTheConcept: Concept,
    connectionTypeString: str,
    actions: Optional[InnerActions] = None
) -> Connection:
    """
    Simplified connection creator that accepts concepts and a type string.

    This is a convenience wrapper around CreateTheConnectionLocal that:
    1. Accepts Concept objects instead of IDs
    2. Creates the connection type concept if it doesn't exist
    3. Extracts necessary IDs automatically
    4. Sets appropriate defaults for external connections (orderId=1000)

    **Advantages:**
    - More intuitive API (pass concepts, not IDs)
    - Automatic type concept creation/retrieval
    - Less boilerplate code

    Args:
        ofTheConcept: The source Concept object (FROM).
        toTheConcept: The target Concept object (TO).
        connectionTypeString: Type name as string (e.g., "the_person_email").
                             A type concept will be created if it doesn't exist.
        actions: Action tracking object for batch operations.

    Returns:
        The created Connection object.

    Example:
        >>> person = await MakeTheInstanceConceptLocal("the_person", "", True, 101)
        >>> email = await MakeTheInstanceConceptLocal("the_email", "alice@example.com", False, 101)
        >>>
        >>> connection = await CreateConnection(person, email, "the_person_email")
        >>> # Connection created with:
        >>> # - ofTheConceptId: person.id
        >>> # - toTheConceptId: email.id
        >>> # - typeId: auto-generated from "the_person_email"
        >>> # - orderId: 1000 (external connection)

    Example:
        >>> # With action tracking
        >>> actions = InnerActions()
        >>> conn1 = await CreateConnection(concept1, concept2, "links_to", actions)
        >>> conn2 = await CreateConnection(concept2, concept3, "links_to", actions)
        >>> print(len(actions.connections))  # 2
    """
    if actions is None:
        actions = InnerActions()

    # Create/retrieve type concept from connection type string
    typeConcept = await MakeTheTypeConceptLocal(
        connectionTypeString,
        sessionId=999,
        sessionUserId=999,
        userId=999,
        actions=actions
    )

    userId = ofTheConcept.userId

    return await CreateTheConnectionLocal(
        ofTheConceptId=ofTheConcept.id,
        toTheConceptId=toTheConcept.id,
        typeId=typeConcept.id,
        orderId=1000,  # External connection
        typeString=connectionTypeString,
        userId=userId,
        actions=actions
    )


async def CreateConnectionBetweenTwoConceptsLocal(
    ofTheConcept: Concept,
    toTheConcept: Concept,
    linker: str,
    both: bool = False,
    actions: Optional[InnerActions] = None
) -> Connection:
    """
    Creates a named connection between two concepts with optional bidirectional linking.

    **Complex Naming Logic:**
    - Forward connection type: "{ofType}_s_{linker}_s" (e.g., "person_s_knows_s")
    - Backward connection type: "{toType}_s_{linker}_by" (e.g., "person_s_knows_by")
    - Uses type.characterValue from concepts to build meaningful connection names

    **Bidirectional Mode (both=True):**
    - Creates two connections: A→B and B→A
    - Forward: ofTheConcept → toTheConcept with "{ofType}_s_{linker}_s"
    - Backward: toTheConcept → ofTheConcept with "{toType}_s_{linker}_by"

    Args:
        ofTheConcept: Source concept (connection starts here).
        toTheConcept: Target concept (connection points here).
        linker: Relationship name (e.g., "knows", "works_at", "has").
        both: If True, creates bidirectional connection (both A→B and B→A).
        actions: Action tracking for batch operations.

    Returns:
        The forward connection object.

    Example:
        >>> # Create unidirectional "Alice knows Bob"
        >>> conn = await CreateConnectionBetweenTwoConceptsLocal(
        ...     aliceConcept,
        ...     bobConcept,
        ...     "knows",
        ...     both=False
        ... )
        >>> # Creates: person_s_knows_s connection from Alice to Bob

    Example:
        >>> # Create bidirectional "Alice friends Bob" (both directions)
        >>> await CreateConnectionBetweenTwoConceptsLocal(
        ...     aliceConcept,
        ...     bobConcept,
        ...     "friends",
        ...     both=True
        ... )
        >>> # Creates: person_s_friends_s (Alice→Bob) AND person_s_friends_by (Bob→Alice)
    """
    if actions is None:
        actions = InnerActions()

    try:
        userId = ofTheConcept.userId

        # Create backward connection if bidirectional
        if both:
            # Build backward linker name: {toType}_s_{linker}_by
            toTypeChar = toTheConcept.type.characterValue if toTheConcept.type else "unknown"
            prefix1 = f"{toTypeChar}_s"
            linkerAdd1 = f"{linker}_by"
            backwardLinker = f"{prefix1}_{linkerAdd1}"

            # Create connection concept for backward link
            connectionConceptReverse = await MakeTheInstanceConceptLocal(
                type="connection",
                referent=backwardLinker,
                composition=False,
                userId=999,
                accessId=999,
                sessionInformationId=999,
                referentId=0,
                actions=actions
            )

            # Create backward connection (to → of)
            await CreateTheConnectionLocal(
                ofTheConceptId=toTheConcept.id,
                toTheConceptId=ofTheConcept.id,
                typeId=connectionConceptReverse.id,
                orderId=1000,
                typeString="",
                userId=userId,
                actions=actions
            )

        # Build forward linker name: {ofType}_s_{linker}_s
        ofTypeChar = ofTheConcept.type.characterValue if ofTheConcept.type else "unknown"
        prefix = f"{ofTypeChar}_s"
        linkerAdd = f"{linker}_s"
        forwardLinker = f"{prefix}_{linkerAdd}"

        # Create connection concept for forward link
        connectionConcept = await MakeTheInstanceConceptLocal(
            type="connection",
            referent=forwardLinker,
            composition=False,
            userId=999,
            accessId=999,
            sessionInformationId=999,
            referentId=0,
            actions=actions
        )

        # Create forward connection (of → to)
        newConnection = await CreateTheConnectionLocal(
            ofTheConceptId=ofTheConcept.id,
            toTheConceptId=toTheConcept.id,
            typeId=connectionConcept.id,
            orderId=1000,
            typeString="",
            userId=userId,
            actions=actions
        )

        return newConnection

    except Exception as error:
        print(f"Error in CreateConnectionBetweenTwoConceptsLocal: {error}")
        raise error
