"""
FortiOS MONITOR - Monitor User Fortitoken Cloud

Monitoring endpoint for monitor user fortitoken cloud data.

API Endpoints:
    GET    /monitor/user/fortitoken_cloud

Example Usage:
    >>> from hfortix.FortiOS import FortiOS
    >>> fgt = FortiOS(host="192.168.1.99", token="your-api-token")
    >>>
    >>> # Get monitoring/log data (read-only)
    >>> data = fgt.api.monitor.user.fortitoken_cloud.get()
    >>>
    >>> # With filters and parameters
    >>> data = fgt.api.monitor.user.fortitoken_cloud.get(
    ...     count=100,
    ...     start=0
    ... )

Note:
    This is a read-only endpoint. Only GET operations are supported.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from hfortix.FortiOS.http_client_interface import IHTTPClient


class Status:
    """
    Status Operations.

    Provides read-only access for FortiOS status data.

    Methods:
        get(): Retrieve monitoring/log data (read-only)

    Note:
        This is a read-only endpoint. Configuration changes are not supported.
    """

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize Status endpoint.

        Args:
            client: HTTPClient instance
        """
        self._client = client

    def get(
        self,
        payload_dict: dict[str, Any] | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Retrieve FortiToken Cloud service status.

        Args:
            payload_dict: Optional dictionary of parameters
            raw_json: Return raw JSON response if True
            **kwargs: Additional parameters as keyword arguments

        Returns:
            Dictionary containing API response

        Example:
            >>> fgt.api.monitor.user.fortitoken_cloud.status.get()
        """
        params = payload_dict.copy() if payload_dict else {}
        params.update(kwargs)
        return self._client.get(
            "monitor",
            "/user/fortitoken-cloud/status",
            params=params
        )


class Trial:
    """Trial operations."""

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize Trial endpoint.

        Args:
            client: HTTPClient instance
        """
        self._client = client

    def post(
        self,
        payload_dict: dict[str, Any] | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Activate FortiToken Cloud trial.

        Args:
            payload_dict: Optional dictionary of parameters
            raw_json: Return raw JSON response if True
            **kwargs: Additional parameters as keyword arguments

        Returns:
            Dictionary containing API response

        Example:
            >>> fgt.api.monitor.user.fortitoken_cloud.trial.post()
        """
        data = payload_dict.copy() if payload_dict else {}
        data.update(kwargs)
        return self._client.post(
            "monitor",
            "/user/fortitoken-cloud/trial",
            data=data
        )


class FortitokenCloud:
    """FortitokenCloud operations."""

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize FortitokenCloud endpoint.

        Args:
            client: HTTPClient instance for API communication
        """
        self._client = client

        # Initialize nested resources
        self.status = Status(client)
        self.trial = Trial(client)
