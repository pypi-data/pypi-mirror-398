"""
Local services for offline-first concept and connection creation and management.

These functions create and manage concepts and connections in local storage without
immediate backend synchronization.
"""

from ccs.services.local.create_the_concept_local import CreateTheConceptLocal
from ccs.services.local.make_the_concept_local import MakeTheConceptLocal
from ccs.services.local.make_the_type_local import MakeTheTypeConceptLocal
from ccs.services.local.make_the_instance_concept_local import MakeTheInstanceConceptLocal
from ccs.services.local.get_concept_by_character_local import GetConceptByCharacterAndCategoryLocal
from ccs.services.local.helpers import SplitStrings
from ccs.services.local.create_the_connection_local import (
    CreateTheConnectionLocal,
    CreateConnection,
    CreateConnectionBetweenTwoConceptsLocal,
)

__all__ = [
    # Concept functions
    "CreateTheConceptLocal",
    "MakeTheConceptLocal",
    "MakeTheTypeConceptLocal",
    "MakeTheInstanceConceptLocal",
    "GetConceptByCharacterAndCategoryLocal",
    "SplitStrings",
    # Connection functions
    "CreateTheConnectionLocal",
    "CreateConnection",
    "CreateConnectionBetweenTwoConceptsLocal",
]
