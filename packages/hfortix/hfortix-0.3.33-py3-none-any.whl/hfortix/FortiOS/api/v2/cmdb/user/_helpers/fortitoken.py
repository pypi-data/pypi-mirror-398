"""
Validation helpers for user fortitoken endpoint.

Each endpoint has its own validation file to keep validation logic
separate and maintainable. Use central cmdb._helpers tools for common tasks.

Auto-generated from OpenAPI specification by generate_validators.py
Customize as needed for endpoint-specific business logic.
"""

from typing import Any

# Valid enum values from API documentation
VALID_BODY_STATUS = ['active', 'lock']
VALID_QUERY_ACTION = ['default', 'schema']

# ============================================================================
# GET Validation
# ============================================================================


def validate_fortitoken_get(
    attr: str | None = None,
    filters: dict[str, Any] | None = None,
    **params: Any
) -> tuple[bool, str | None]:
    """
    Validate GET request parameters.

    Args:
        attr: Attribute filter (optional)
        filters: Additional filter parameters
        **params: Other query parameters

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> # List all objects
        >>> is_valid, error = {func_name}()
    """
    # Validate query parameters if present
    if 'action' in params:
        value = params.get('action')
        if value and value not in VALID_QUERY_ACTION:
            return (
                False,
                f"Invalid query parameter 'action'='{value}'. Must be one of: "
                f"{', '.join(VALID_QUERY_ACTION)}"
            )

    return (True, None)


# ============================================================================
# POST Validation
# ============================================================================


def validate_fortitoken_post(
        payload: dict[str, Any]) -> tuple[bool, str | None]:
    """
    Validate POST request payload for creating fortitoken.

    Args:
        payload: The payload to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate serial-number if present
    if 'serial-number' in payload:
        value = payload.get('serial-number')
        if value and isinstance(value, str) and len(value) > 16:
            return (False, "serial-number cannot exceed 16 characters")

    # Validate status if present
    if 'status' in payload:
        value = payload.get('status')
        if value and value not in VALID_BODY_STATUS:
            return (
                False,
                f"Invalid status '{value}'. Must be one of: "
                f"{', '.join(VALID_BODY_STATUS)}"
            )

    # Validate seed if present
    if 'seed' in payload:
        value = payload.get('seed')
        if value and isinstance(value, str) and len(value) > 208:
            return (False, "seed cannot exceed 208 characters")

    # Validate comments if present
    if 'comments' in payload:
        value = payload.get('comments')
        if value and isinstance(value, str) and len(value) > 255:
            return (False, "comments cannot exceed 255 characters")

    # Validate license if present
    if 'license' in payload:
        value = payload.get('license')
        if value and isinstance(value, str) and len(value) > 31:
            return (False, "license cannot exceed 31 characters")

    # Validate activation-code if present
    if 'activation-code' in payload:
        value = payload.get('activation-code')
        if value and isinstance(value, str) and len(value) > 32:
            return (False, "activation-code cannot exceed 32 characters")

    # Validate activation-expire if present
    if 'activation-expire' in payload:
        value = payload.get('activation-expire')
        if value is not None:
            try:
                int_val = int(value)
                if int_val < 0 or int_val > 4294967295:
                    return (
                        False,
                        "activation-expire must be between 0 and 4294967295"
                    )
            except (ValueError, TypeError):
                return (
                    False,
                    f"activation-expire must be numeric, "
                    f"got: {value}"
                )

    # Validate reg-id if present
    if 'reg-id' in payload:
        value = payload.get('reg-id')
        if value and isinstance(value, str) and len(value) > 256:
            return (False, "reg-id cannot exceed 256 characters")

    # Validate os-ver if present
    if 'os-ver' in payload:
        value = payload.get('os-ver')
        if value and isinstance(value, str) and len(value) > 15:
            return (False, "os-ver cannot exceed 15 characters")

    return (True, None)
