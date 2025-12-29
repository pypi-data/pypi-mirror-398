"""
Make instance concept locally - the core building block of the concept-connection system.

This is THE fundamental function for creating concepts in local storage. It implements
an intelligent get-or-create pattern that checks for existing concepts before creating
new ones, preventing duplicates while supporting both unique instances and composition concepts.
"""

from typing import Optional

from ccs.models.concept import Concept
from ccs.data.local_concept_data import LocalConceptsData
from ccs.data.local_sync_data import LocalSyncData
from ccs.data.inner_actions import InnerActions
from ccs.services.local.make_the_type_local import MakeTheTypeConceptLocal
from ccs.services.local.create_the_concept_local import CreateTheConceptLocal


async def MakeTheInstanceConceptLocal(
    type: str,
    referent: str,
    composition: bool = False,
    userId: int = 0,
    accessId: int = 4,
    sessionInformationId: int = 999,
    referentId: int = 0,
    actions: Optional[InnerActions] = None
) -> Concept:
    """
    Creates or retrieves an instance concept locally - the core building block of the concept-connection system.

    This is THE fundamental function for creating concepts in local storage. It implements an intelligent
    get-or-create pattern that checks for existing concepts before creating new ones, preventing duplicates
    while supporting both unique instances and composition concepts.

    **Core Behaviors:**

    1. **Composition Mode (composition=True)**: Always creates a new concept
       - Used for containers/objects that need unique instances
       - Marks concept with isComposition flag
       - Example: Each "Project" is unique, even with same name

    2. **Instance Mode (composition=False)**: Get-or-create pattern
       - Checks if concept with same type and value exists
       - Returns existing if found (deduplication)
       - Creates new only if not found
       - Example: "Published" status concept reused across items

    3. **Long Text Handling**: Values >255 characters always create new
       - Prevents expensive lookups on large text
       - Each long text gets unique concept

    **Type String Processing:**
    - **Best Practice**: Always pass type with "the_" prefix (e.g., "the_name", "the_email")
    - Auto-correction: If missing, "the_" is automatically added internally
      - "name" → "the_name" (auto-corrected)
      - "email" → "the_email" (auto-corrected)
      - "the_status" → "the_status" (already correct)
    - Creates type concept if it doesn't exist
    - **Recommendation**: Use explicit "the_" prefix for code clarity and consistency

    **Sync and Storage:**
    - Adds concept to LocalSyncData queue for backend sync
    - Stores in LocalConceptsData (local memory)
    - Tracks in actions parameter for batch operations
    - Assigns negative ID (virtual/local)

    **Process Flow:**
    1. Normalizes type string (adds "the_" prefix)
    2. Creates/retrieves type concept via MakeTheTypeConceptLocal
    3. If composition=True: Creates new concept immediately
    4. If referent length >255: Creates new concept
    5. If regular instance: Checks for existing by type+value
    6. Returns existing or creates new
    7. Attaches type information
    8. Adds to sync queue

    Args:
        type: The type/key of the concept. **Should follow the format "the_xyz"**.
              Represents what kind of data this is.
              Examples: "the_name", "the_email", "the_status", "the_first_name"

              **Note**: If you pass without "the_" prefix (e.g., "name"), the code will
              automatically add it internally (becomes "the_name"). However, best practice
              is to always include the "the_" prefix for clarity and consistency.

        referent: The actual value/content of the concept.
                 The human-readable data (e.g., "Alice", "alice@example.com", "Active").
                 Can be empty string for composition concepts.

        composition: Boolean flag determining creation behavior.
                    - True: Always creates new concept (unique instances)
                    - False: Get-or-create pattern (reuses existing)
                    Defaults to False.

        userId: The ID of the user creating this concept. Used for ownership and permissions.

        accessId: Access control level. Typically 4 (default internal access).
                  Controls who can view/modify this concept.

        sessionInformationId: Session identifier for tracking. Defaults to 999 (system).
                               Used for audit logging and session management.

        referentId: Optional reference to another concept ID.
                    Used when this concept is an instance of or refers to another concept.
                    Defaults to 0 (no reference).

        actions: Action tracking object that accumulates all created concepts and connections.
                Used for batch operations, rollback, and sync management.

    Returns:
        The created or retrieved Concept object with:
        - Negative ID if newly created locally
        - Attached type information (concept.type)
        - All standard concept properties

    Example:
        >>> # Create a reusable status concept (get-or-create)
        >>> status = await MakeTheInstanceConceptLocal(
        ...     type="the_status",       # type (with "the_" prefix - best practice)
        ...     referent="Active",       # value
        ...     composition=False,       # not composition - will reuse if exists
        ...     userId=101,
        ...     accessId=4,
        ...     sessionInformationId=999,
        ...     referentId=0
        ... )
        >>> # First call creates, subsequent calls return same concept

    Example:
        >>> # Create a composition concept (always new)
        >>> project = await MakeTheInstanceConceptLocal(
        ...     type="the_project",      # type (with "the_" prefix)
        ...     referent="Project Alpha",# value
        ...     composition=True,        # composition - always creates new
        ...     userId=101,
        ...     accessId=4
        ... )
        >>> # Each project is unique, even with same name
        >>> print(project.isComposition)  # True

    Example:
        >>> # Type prefix is added automatically if missing (but prefer explicit)
        >>> email = await MakeTheInstanceConceptLocal(
        ...     type="email",            # Missing "the_" - will become "the_email" internally
        ...     referent="alice@example.com",
        ...     composition=False,
        ...     userId=101
        ... )
        >>> print(email.typeCharacter)  # "the_email" (auto-prefixed)

    Example:
        >>> # Track actions for batch operations
        >>> actions = InnerActions()
        >>> await MakeTheInstanceConceptLocal("the_name", "Alice", False, 101, 4, 999, 0, actions)
        >>> await MakeTheInstanceConceptLocal("the_email", "alice@ex.com", False, 101, 4, 999, 0, actions)
        >>> print(len(actions.concepts))  # 2 (plus any type concepts created)

    Example:
        >>> # Deduplication in action
        >>> status1 = await MakeTheInstanceConceptLocal("the_status", "Published", False, 101, 4)
        >>> status2 = await MakeTheInstanceConceptLocal("the_status", "Published", False, 101, 4)
        >>> print(status1.id == status2.id)  # True - same concept reused

    Raises:
        Exception: Re-raises any errors from underlying functions.
                  Common issues: Type concept creation failures, storage errors.

    See Also:
        CreateTheConceptLocal: For the underlying creation function
        MakeTheTypeConceptLocal: For type concept creation/retrieval
        LocalConceptsData.GetConceptByCharacterAndTypeLocal: For existence check
        LocalSyncData.AddConcept: For sync queue management
    """
    if actions is None:
        actions = InnerActions()

    try:
        # Local defaults (matching JS implementation)
        sessionInformationId = 999
        categoryId = 4
        sessionInformationUserId = userId
        accessId = 4

        stringToCheck = ""
        stringLength = len(referent)

        typeConcept: Optional[Concept] = None
        concept: Concept

        # Check if type already has "the_" prefix
        startsWithThe = type.startswith("the_")

        if startsWithThe:
            stringToCheck = type
        else:
            stringToCheck = "the_" + type

        # Branch based on composition flag and string length
        if composition:
            # Composition mode: always create new concept
            typeConcept = await MakeTheTypeConceptLocal(
                type,
                sessionInformationId,
                userId,
                userId,
                actions
            )

            concept = await CreateTheConceptLocal(
                referent=referent,
                typecharacter=type,
                userId=userId,
                categoryId=categoryId,
                typeId=typeConcept.id,
                accessId=accessId,
                isComposition=True,
                referentId=referentId,
                actions=actions
            )

        elif stringLength > 255:
            # Long text: always create new concept (skip lookup)
            typeConcept = await MakeTheTypeConceptLocal(
                stringToCheck,
                sessionInformationId,
                sessionInformationUserId,
                userId,
                actions
            )

            concept = await CreateTheConceptLocal(
                referent=referent,
                typecharacter=stringToCheck,
                userId=userId,
                categoryId=categoryId,
                typeId=typeConcept.id,
                accessId=accessId,
                isComposition=False,
                referentId=None,
                actions=actions
            )

        else:
            # Instance mode: get-or-create pattern
            typeConcept = await MakeTheTypeConceptLocal(
                stringToCheck,
                sessionInformationId,
                sessionInformationUserId,
                userId,
                actions
            )

            # Check for existing concept with same character value and type
            conceptTypeCharacter = LocalConceptsData.GetConceptByCharacterAndTypeLocal(
                referent, typeConcept.id
            )
            concept = conceptTypeCharacter

            # If not found (id == 0 and userId == 0), create new
            if conceptTypeCharacter.id == 0 and conceptTypeCharacter.userId == 0:
                concept = await CreateTheConceptLocal(
                    referent=referent,
                    typecharacter=stringToCheck,
                    userId=userId,
                    categoryId=categoryId,
                    typeId=typeConcept.id,
                    accessId=accessId,
                    isComposition=False,
                    referentId=None,
                    actions=actions
                )

        # Attach type information to the concept
        concept.type = typeConcept

        # Add to sync queue for later backend sync
        LocalSyncData.AddConcept(concept)

        # Track in actions
        actions.concepts.append(concept)

        return concept

    except Exception as error:
        # Log and re-raise for handling by caller
        raise error
