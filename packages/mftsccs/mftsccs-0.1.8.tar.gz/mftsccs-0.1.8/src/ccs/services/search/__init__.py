"""
Search services for CCS library.

This module contains functions for formatting and processing query results,
converting graph structures (concepts and connections) into JSON format.
"""

from ccs.services.search.count_info import CountInfo, decode_count_info, get_connection_type_for_count
from ccs.services.search.ordering import order_connections
from ccs.services.search.prefetch import get_connection_data_prefetch
from ccs.services.search.data_id_format import (
    format_connections_data_id,
    format_function_data,
    format_function_data_for_data,
    format_from_connections_altered_array_external,
)
from ccs.services.search.flatten import (
    flatten_query_result,
    flatten_to_simple,
    flatten_to_records,
)

__all__ = [
    "CountInfo",
    "decode_count_info",
    "get_connection_type_for_count",
    "order_connections",
    "get_connection_data_prefetch",
    "format_connections_data_id",
    "format_function_data",
    "format_function_data_for_data",
    "format_from_connections_altered_array_external",
    "flatten_query_result",
    "flatten_to_simple",
    "flatten_to_records",
]
