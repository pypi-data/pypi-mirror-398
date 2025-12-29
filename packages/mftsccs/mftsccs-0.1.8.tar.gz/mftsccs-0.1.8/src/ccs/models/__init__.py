"""
Data models for the CCS library.
"""

from ccs.models.concept import Concept, create_default_concept
from ccs.models.connection import Connection, create_default_connection

__all__ = [
    "Concept",
    "create_default_concept",
    "Connection",
    "create_default_connection",
]
