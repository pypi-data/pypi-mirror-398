"""
Helpers module for FortiOS API endpoints.

Provides shared helper functions to eliminate code duplication
across all API resource types (CMDB, Monitor, etc.).

Includes functions for:
- Payload building (snake_case to kebab-case conversion)
- List normalization (various formats to FortiOS [{'name': '...'}] format)
- Type conversion (bool to enable/disable, etc.)
- Data cleaning and filtering
- Validation helpers

This is the central API helpers module that can be used by:
- hfortix.FortiOS.api.v2.cmdb.* (Configuration endpoints)
- hfortix.FortiOS.api.v2.monitor.* (Monitoring endpoints)
- Any other API categories
"""

from .helpers import (
    build_cmdb_payload,
    build_cmdb_payload_normalized,
    convert_boolean_to_str,
    filter_empty_values,
    normalize_member_list,
    normalize_to_name_list,
    validate_required_fields,
)

__all__ = [
    "build_cmdb_payload",
    "build_cmdb_payload_normalized",
    "normalize_to_name_list",
    "normalize_member_list",
    "filter_empty_values",
    "validate_required_fields",
    "convert_boolean_to_str",
]
