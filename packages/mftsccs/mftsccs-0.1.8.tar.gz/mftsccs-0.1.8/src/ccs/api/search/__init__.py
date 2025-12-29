"""
Search API functions for CCS library.
"""

from ccs.api.search.freeschema_query_api import freeschema_query_api
from ccs.api.search.schema_query_listener import schema_query_listener

__all__ = [
    "freeschema_query_api",
    "schema_query_listener",
]
