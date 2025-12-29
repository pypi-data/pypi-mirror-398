"""
Services for the CCS library.

Contains business logic for concept creation, retrieval, and management.
"""

from ccs.services.local import (
    CreateTheConceptLocal,
    MakeTheConceptLocal,
    MakeTheTypeConceptLocal,
    MakeTheInstanceConceptLocal,
    GetConceptByCharacterAndCategoryLocal,
    SplitStrings,
    # Connection functions
    CreateTheConnectionLocal,
    CreateConnection,
    CreateConnectionBetweenTwoConceptsLocal,
)

from ccs.services.get import (
    GetTheConcept,
    AddTypeConcept,
)

__all__ = [
    # Local services - Concepts
    "CreateTheConceptLocal",
    "MakeTheConceptLocal",
    "MakeTheTypeConceptLocal",
    "MakeTheInstanceConceptLocal",
    "GetConceptByCharacterAndCategoryLocal",
    "SplitStrings",
    # Local services - Connections
    "CreateTheConnectionLocal",
    "CreateConnection",
    "CreateConnectionBetweenTwoConceptsLocal",
    # Get services
    "GetTheConcept",
    "AddTypeConcept",
]
