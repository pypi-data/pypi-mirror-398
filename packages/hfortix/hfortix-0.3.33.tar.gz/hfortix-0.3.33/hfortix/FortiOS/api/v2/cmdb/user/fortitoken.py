"""
FortiOS CMDB - Cmdb User Fortitoken

Configuration endpoint for managing cmdb user fortitoken objects.

API Endpoints:
    GET    /cmdb/user/fortitoken
    POST   /cmdb/user/fortitoken
    GET    /cmdb/user/fortitoken
    PUT    /cmdb/user/fortitoken/{identifier}
    DELETE /cmdb/user/fortitoken/{identifier}

Example Usage:
    >>> from hfortix.FortiOS import FortiOS
    >>> fgt = FortiOS(host="192.168.1.99", token="your-api-token")
    >>>
    >>> # List all items
    >>> items = fgt.api.cmdb.user.fortitoken.get()
    >>>
    >>> # Get specific item (if supported)
    >>> item = fgt.api.cmdb.user.fortitoken.get(name="item_name")
    >>>
    >>> # Create new item (use POST)
    >>> result = fgt.api.cmdb.user.fortitoken.post(
    ...     name="new_item",
    ...     # ... additional parameters
    ... )
    >>>
    >>> # Update existing item (use PUT)
    >>> result = fgt.api.cmdb.user.fortitoken.put(
    ...     name="existing_item",
    ...     # ... parameters to update
    ... )
    >>>
    >>> # Delete item
    >>> result = fgt.api.cmdb.user.fortitoken.delete(name="item_name")

Important:
    - Use **POST** to create new objects (404 error if already exists)
    - Use **PUT** to update existing objects (404 error if doesn't exist)
    - Use **GET** to retrieve configuration (no changes made)
    - Use **DELETE** to remove objects (404 error if doesn't exist)
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING, Union, cast

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from hfortix.FortiOS.http_client_interface import IHTTPClient


class Fortitoken:
    """
    Fortitoken Operations.

    Provides CRUD operations for FortiOS fortitoken configuration.

    Methods:
        get(): Retrieve configuration objects
        post(): Create new configuration objects
        put(): Update existing configuration objects
        delete(): Remove configuration objects

    Important:
        - POST creates new objects (404 if name already exists)
        - PUT updates existing objects (404 if name doesn't exist)
        - GET retrieves objects without making changes
        - DELETE removes objects (404 if name doesn't exist)
    """

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize Fortitoken endpoint.

        Args:
            client: HTTPClient instance for API communication
        """
        self._client = client

    def get(
        self,
        serial_number: str | None = None,
        payload_dict: dict[str, Any] | None = None,
        attr: str | None = None,
        skip_to_datasource: dict | None = None,
        acs: int | None = None,
        search: str | None = None,
        vdom: str | bool | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Select a specific entry from a CLI table.

        Args:
            serial_number: Object identifier (optional for list, required for
            specific)
            attr: Attribute name that references other table (optional)
            skip_to_datasource: Skip to provided table's Nth entry. E.g
            {datasource: 'firewall.address', pos: 10, global_entry: false}
            (optional)
            acs: If true, returned result are in ascending order. (optional)
            search: If present, the objects will be filtered by the search
            value. (optional)
            vdom: Virtual domain name, or False to skip. Handled by HTTPClient.
            raw_json: If True, return full API response with metadata. If
            False, return only results.
            **kwargs: Additional query parameters (filter, sort, start, count,
            format, etc.)

        Common Query Parameters (via **kwargs):
            filter: Filter results (e.g., filter='name==value')
            sort: Sort results (e.g., sort='name,asc')
            start: Starting entry index for paging
            count: Maximum number of entries to return
            format: Fields to return (e.g., format='name|type')
            See FortiOS REST API documentation for full list of query
            parameters

        Returns:
            Dictionary containing API response
        """
        params = payload_dict.copy() if payload_dict else {}

        # Build endpoint path
        if serial_number:
            endpoint = f"/user/fortitoken/{serial_number}"
        else:
            endpoint = "/user/fortitoken"
        if attr is not None:
            params['attr'] = attr
        if skip_to_datasource is not None:
            params['skip_to_datasource'] = skip_to_datasource
        if acs is not None:
            params['acs'] = acs
        if search is not None:
            params['search'] = search
        params.update(kwargs)
        return self._client.get(
            "cmdb",
            endpoint,
            params=params,
            vdom=vdom,
            raw_json=raw_json
        )

    def put(
        self,
        serial_number: str | None = None,
        payload_dict: dict[str, Any] | None = None,
        before: str | None = None,
        after: str | None = None,
        status: str | None = None,
        seed: str | None = None,
        comments: str | None = None,
        license: str | None = None,
        activation_code: str | None = None,
        activation_expire: int | None = None,
        reg_id: str | None = None,
        os_ver: str | None = None,
        vdom: str | bool | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Update this specific resource.

        Args:
            payload_dict: Optional dictionary of all parameters (can be passed
            as first positional arg)
            serial_number: Object identifier (required)
            before: If *action=move*, use *before* to specify the ID of the
            resource that this resource will be moved before. (optional)
            after: If *action=move*, use *after* to specify the ID of the
            resource that this resource will be moved after. (optional)
            serial_number: Serial number. (optional)
            status: Status. (optional)
            seed: Token seed. (optional)
            comments: Comment. (optional)
            license: Mobile token license. (optional)
            activation_code: Mobile token user activation-code. (optional)
            activation_expire: Mobile token user activation-code expire time.
            (optional)
            reg_id: Device Reg ID. (optional)
            os_ver: Device Mobile Version. (optional)
            vdom: Virtual domain name, or False to skip. Handled by HTTPClient.
            raw_json: If True, return full API response with metadata. If
            False, return only results.
            **kwargs: Additional query parameters (filter, sort, start, count,
            format, etc.)

        Common Query Parameters (via **kwargs):
            filter: Filter results (e.g., filter='name==value')
            sort: Sort results (e.g., sort='name,asc')
            start: Starting entry index for paging
            count: Maximum number of entries to return
            format: Fields to return (e.g., format='name|type')
            See FortiOS REST API documentation for full list of query
            parameters

        Returns:
            Dictionary containing API response
        """
        data_payload = payload_dict.copy() if payload_dict else {}

        # Build endpoint path
        if not serial_number:
            raise ValueError("serial_number is required for put()")
        endpoint = f"/user/fortitoken/{serial_number}"
        if before is not None:
            data_payload['before'] = before
        if after is not None:
            data_payload['after'] = after
        if serial_number is not None:
            data_payload['serial-number'] = serial_number
        if status is not None:
            data_payload['status'] = status
        if seed is not None:
            data_payload['seed'] = seed
        if comments is not None:
            data_payload['comments'] = comments
        if license is not None:
            data_payload['license'] = license
        if activation_code is not None:
            data_payload['activation-code'] = activation_code
        if activation_expire is not None:
            data_payload['activation-expire'] = activation_expire
        if reg_id is not None:
            data_payload['reg-id'] = reg_id
        if os_ver is not None:
            data_payload['os-ver'] = os_ver
        data_payload.update(kwargs)
        return self._client.put(
            "cmdb",
            endpoint,
            data=data_payload,
            vdom=vdom,
            raw_json=raw_json
        )

    def delete(
        self,
        serial_number: str | None = None,
        payload_dict: dict[str, Any] | None = None,
        vdom: str | bool | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Delete this specific resource.

        Args:
            serial_number: Object identifier (required)
            vdom: Virtual domain name, or False to skip. Handled by HTTPClient.
            raw_json: If True, return full API response with metadata. If
            False, return only results.
            **kwargs: Additional query parameters (filter, sort, start, count,
            format, etc.)

        Common Query Parameters (via **kwargs):
            filter: Filter results (e.g., filter='name==value')
            sort: Sort results (e.g., sort='name,asc')
            start: Starting entry index for paging
            count: Maximum number of entries to return
            format: Fields to return (e.g., format='name|type')
            See FortiOS REST API documentation for full list of query
            parameters

        Returns:
            Dictionary containing API response
        """
        params = payload_dict.copy() if payload_dict else {}

        # Build endpoint path
        if not serial_number:
            raise ValueError("serial_number is required for delete()")
        endpoint = f"/user/fortitoken/{serial_number}"
        params.update(kwargs)
        return self._client.delete(
            "cmdb",
            endpoint,
            params=params,
            vdom=vdom,
            raw_json=raw_json
        )

    def exists(
        self,
        serial_number: str,
        vdom: str | bool | None = None,
    ) -> Union[bool, Coroutine[Any, Any, bool]]:
        """
        Check if an object exists.

        Args:
            serial_number: Object identifier
            vdom: Virtual domain name, or False to skip. Handled by HTTPClient.

        Returns:
            True if object exists, False otherwise
        """
        import inspect

        from hfortix.FortiOS.exceptions_forti import ResourceNotFoundError

        # Call get() - returns dict (sync) or coroutine (async)
        result = self.get(serial_number=serial_number, vdom=vdom)

        # Check if async mode
        if inspect.iscoroutine(result):
            async def _async():
                try:
                    # Runtime check confirms result is a coroutine, cast for
                    # mypy
                    await cast(Coroutine[Any, Any, dict[str, Any]], result)
                    return True
                except ResourceNotFoundError:
                    return False
            # Type ignore justified: mypy can't verify Union return type
            # narrowing

            return _async()
        # Sync mode - get() already executed, no exception means it exists
        return True

    def post(
        self,
        payload_dict: dict[str, Any] | None = None,
        nkey: str | None = None,
        serial_number: str | None = None,
        status: str | None = None,
        seed: str | None = None,
        comments: str | None = None,
        license: str | None = None,
        activation_code: str | None = None,
        activation_expire: int | None = None,
        reg_id: str | None = None,
        os_ver: str | None = None,
        vdom: str | bool | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Create object(s) in this table.

        Args:
            payload_dict: Optional dictionary of all parameters (can be passed
            as first positional arg)
            nkey: If *action=clone*, use *nkey* to specify the ID for the new
            resource to be created. (optional)
            serial_number: Serial number. (optional)
            status: Status. (optional)
            seed: Token seed. (optional)
            comments: Comment. (optional)
            license: Mobile token license. (optional)
            activation_code: Mobile token user activation-code. (optional)
            activation_expire: Mobile token user activation-code expire time.
            (optional)
            reg_id: Device Reg ID. (optional)
            os_ver: Device Mobile Version. (optional)
            vdom: Virtual domain name, or False to skip. Handled by HTTPClient.
            raw_json: If True, return full API response with metadata. If
            False, return only results.
            **kwargs: Additional query parameters (filter, sort, start, count,
            format, etc.)

        Common Query Parameters (via **kwargs):
            filter: Filter results (e.g., filter='name==value')
            sort: Sort results (e.g., sort='name,asc')
            start: Starting entry index for paging
            count: Maximum number of entries to return
            format: Fields to return (e.g., format='name|type')
            See FortiOS REST API documentation for full list of query
            parameters

        Returns:
            Dictionary containing API response
        """
        data_payload = payload_dict.copy() if payload_dict else {}
        endpoint = "/user/fortitoken"
        if nkey is not None:
            data_payload['nkey'] = nkey
        if serial_number is not None:
            data_payload['serial-number'] = serial_number
        if status is not None:
            data_payload['status'] = status
        if seed is not None:
            data_payload['seed'] = seed
        if comments is not None:
            data_payload['comments'] = comments
        if license is not None:
            data_payload['license'] = license
        if activation_code is not None:
            data_payload['activation-code'] = activation_code
        if activation_expire is not None:
            data_payload['activation-expire'] = activation_expire
        if reg_id is not None:
            data_payload['reg-id'] = reg_id
        if os_ver is not None:
            data_payload['os-ver'] = os_ver
        data_payload.update(kwargs)
        return self._client.post(
            "cmdb",
            endpoint,
            data=data_payload,
            vdom=vdom,
            raw_json=raw_json
        )
