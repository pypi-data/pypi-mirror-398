"""
Utilities module for Salesforce Toolkit.

Provides helper functions for common operations.
"""

from kinetic_core.utils.helpers import (
    sanitize_soql,
    build_soql_query,
    validate_salesforce_id,
    chunk_list,
    format_datetime_for_sf,
    parse_sf_datetime,
    extract_field_names_from_query,
    get_sobject_from_id,
    flatten_dict,
    unflatten_dict,
    compare_records,
    generate_external_id,
    batch_records
)

__all__ = [
    "sanitize_soql",
    "build_soql_query",
    "validate_salesforce_id",
    "chunk_list",
    "format_datetime_for_sf",
    "parse_sf_datetime",
    "extract_field_names_from_query",
    "get_sobject_from_id",
    "flatten_dict",
    "unflatten_dict",
    "compare_records",
    "generate_external_id",
    "batch_records"
]
