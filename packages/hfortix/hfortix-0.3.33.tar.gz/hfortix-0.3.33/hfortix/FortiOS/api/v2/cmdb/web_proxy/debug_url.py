"""
FortiOS CMDB - Cmdb Web Proxy Debug Url

Configuration endpoint for managing cmdb web proxy debug url objects.

API Endpoints:
    GET    /cmdb/web-proxy/debug_url
    POST   /cmdb/web-proxy/debug_url
    GET    /cmdb/web-proxy/debug_url
    PUT    /cmdb/web-proxy/debug_url/{identifier}
    DELETE /cmdb/web-proxy/debug_url/{identifier}

Example Usage:
    >>> from hfortix.FortiOS import FortiOS
    >>> fgt = FortiOS(host="192.168.1.99", token="your-api-token")
    >>>
    >>> # List all items
    >>> items = fgt.api.cmdb.web_proxy.debug_url.get()
    >>>
    >>> # Get specific item (if supported)
    >>> item = fgt.api.cmdb.web_proxy.debug_url.get(name="item_name")
    >>>
    >>> # Create new item (use POST)
    >>> result = fgt.api.cmdb.web_proxy.debug_url.post(
    ...     name="new_item",
    ...     # ... additional parameters
    ... )
    >>>
    >>> # Update existing item (use PUT)
    >>> result = fgt.api.cmdb.web_proxy.debug_url.put(
    ...     name="existing_item",
    ...     # ... parameters to update
    ... )
    >>>
    >>> # Delete item
    >>> result = fgt.api.cmdb.web_proxy.debug_url.delete(name="item_name")

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


class DebugUrl:
    """
    Debugurl Operations.

    Provides CRUD operations for FortiOS debugurl configuration.

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
        Initialize DebugUrl endpoint.

        Args:
            client: HTTPClient instance for API communication
        """
        self._client = client

    def get(
        self,
        name: str | None = None,
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
            name: Object identifier (optional for list, required for specific)
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
        if name:
            endpoint = f"/web-proxy/debug-url/{name}"
        else:
            endpoint = "/web-proxy/debug-url"
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
        name: str | None = None,
        payload_dict: dict[str, Any] | None = None,
        before: str | None = None,
        after: str | None = None,
        url_pattern: str | None = None,
        status: str | None = None,
        exact: str | None = None,
        vdom: str | bool | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Update this specific resource.

        Args:
            payload_dict: Optional dictionary of all parameters (can be passed
            as first positional arg)
            name: Object identifier (required)
            before: If *action=move*, use *before* to specify the ID of the
            resource that this resource will be moved before. (optional)
            after: If *action=move*, use *after* to specify the ID of the
            resource that this resource will be moved after. (optional)
            name: Debug URL name. (optional)
            url_pattern: URL exemption pattern. (optional)
            status: Enable/disable this URL exemption. (optional)
            exact: Enable/disable matching the exact path. (optional)
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
        if not name:
            raise ValueError("name is required for put()")
        endpoint = f"/web-proxy/debug-url/{name}"
        if before is not None:
            data_payload['before'] = before
        if after is not None:
            data_payload['after'] = after
        if name is not None:
            data_payload['name'] = name
        if url_pattern is not None:
            data_payload['url-pattern'] = url_pattern
        if status is not None:
            data_payload['status'] = status
        if exact is not None:
            data_payload['exact'] = exact
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
        name: str | None = None,
        payload_dict: dict[str, Any] | None = None,
        vdom: str | bool | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Delete this specific resource.

        Args:
            name: Object identifier (required)
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
        if not name:
            raise ValueError("name is required for delete()")
        endpoint = f"/web-proxy/debug-url/{name}"
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
        name: str,
        vdom: str | bool | None = None,
    ) -> Union[bool, Coroutine[Any, Any, bool]]:
        """
        Check if an object exists.

        Args:
            name: Object identifier
            vdom: Virtual domain name, or False to skip. Handled by HTTPClient.

        Returns:
            True if object exists, False otherwise
        """
        import inspect

        from hfortix.FortiOS.exceptions_forti import ResourceNotFoundError

        # Call get() - returns dict (sync) or coroutine (async)
        result = self.get(name=name, vdom=vdom)

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
        name: str | None = None,
        url_pattern: str | None = None,
        status: str | None = None,
        exact: str | None = None,
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
            name: Debug URL name. (optional)
            url_pattern: URL exemption pattern. (optional)
            status: Enable/disable this URL exemption. (optional)
            exact: Enable/disable matching the exact path. (optional)
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
        endpoint = "/web-proxy/debug-url"
        if nkey is not None:
            data_payload['nkey'] = nkey
        if name is not None:
            data_payload['name'] = name
        if url_pattern is not None:
            data_payload['url-pattern'] = url_pattern
        if status is not None:
            data_payload['status'] = status
        if exact is not None:
            data_payload['exact'] = exact
        data_payload.update(kwargs)
        return self._client.post(
            "cmdb",
            endpoint,
            data=data_payload,
            vdom=vdom,
            raw_json=raw_json
        )
