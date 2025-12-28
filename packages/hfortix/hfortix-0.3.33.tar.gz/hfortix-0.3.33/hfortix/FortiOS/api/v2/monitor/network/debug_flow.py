"""
FortiOS MONITOR - Monitor Network Debug Flow

Monitoring endpoint for monitor network debug flow data.

API Endpoints:
    GET    /monitor/network/debug_flow

Example Usage:
    >>> from hfortix.FortiOS import FortiOS
    >>> fgt = FortiOS(host="192.168.1.99", token="your-api-token")
    >>>
    >>> # Get monitoring/log data (read-only)
    >>> data = fgt.api.monitor.network.debug_flow.get()
    >>>
    >>> # With filters and parameters
    >>> data = fgt.api.monitor.network.debug_flow.get(
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


class Start:
    """
    Start Operations.

    Provides read-only access for FortiOS start data.

    Methods:
        get(): Retrieve monitoring/log data (read-only)

    Note:
        This is a read-only endpoint. Configuration changes are not supported.
    """

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize Start endpoint.

        Args:
            client: HTTPClient instance
        """
        self._client = client

    def post(
        self,
        num_packets: int | None = None,
        ipv6: bool | None = None,
        negate: bool | None = None,
        addr_from: str | None = None,
        addr_to: str | None = None,
        daddr_from: str | None = None,
        daddr_to: str | None = None,
        saddr_from: str | None = None,
        saddr_to: str | None = None,
        port_from: int | None = None,
        port_to: int | None = None,
        dport_from: int | None = None,
        dport_to: int | None = None,
        sport_from: int | None = None,
        sport_to: int | None = None,
        proto: int | None = None,
        payload_dict: dict[str, Any] | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Start debug flow packet capture.

        Args:
            num_packets: Number of packets. (optional)
            ipv6: Whether we are debugging IPv6 traffic. (optional)
            negate: Inverse IPv4 or IPv6 filter. (optional)
            addr_from: IPv4 or IPv6 address start of range. (optional)
            addr_to: IPv4 or IPv6 address end of range. (optional)
            daddr_from: Destination IPv4 or IPv6 address start of range.
            (optional)
            daddr_to: Destination IPv4 or IPv6 address end of range. (optional)
            saddr_from: Source IPv4 or IPv6 address start of range. (optional)
            saddr_to: Source IPv4 or IPv6 address end of range. (optional)
            port_from: Port from. (optional)
            port_to: Port to. (optional)
            dport_from: Destination port from. (optional)
            dport_to: Destination port to. (optional)
            sport_from: Source port from. (optional)
            sport_to: Source port to. (optional)
            proto: Protocol number. (optional)
            payload_dict: Optional dictionary of parameters
            raw_json: Return raw JSON response if True
            **kwargs: Additional parameters as keyword arguments

        Returns:
            Dictionary containing API response

        Example:
            >>> fgt.api.monitor.network.debug_flow.start.post()
        """
        data = payload_dict.copy() if payload_dict else {}
        if num_packets is not None:
            data['num_packets'] = num_packets
        if ipv6 is not None:
            data['ipv6'] = ipv6
        if negate is not None:
            data['negate'] = negate
        if addr_from is not None:
            data['addr_from'] = addr_from
        if addr_to is not None:
            data['addr_to'] = addr_to
        if daddr_from is not None:
            data['daddr_from'] = daddr_from
        if daddr_to is not None:
            data['daddr_to'] = daddr_to
        if saddr_from is not None:
            data['saddr_from'] = saddr_from
        if saddr_to is not None:
            data['saddr_to'] = saddr_to
        if port_from is not None:
            data['port_from'] = port_from
        if port_to is not None:
            data['port_to'] = port_to
        if dport_from is not None:
            data['dport_from'] = dport_from
        if dport_to is not None:
            data['dport_to'] = dport_to
        if sport_from is not None:
            data['sport_from'] = sport_from
        if sport_to is not None:
            data['sport_to'] = sport_to
        if proto is not None:
            data['proto'] = proto
        data.update(kwargs)
        return self._client.post(
            "monitor",
            "/network/debug-flow/start",
            data=data
        )


class Stop:
    """Stop operations."""

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize Stop endpoint.

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
        Stop debug flow packet capture.

        Args:
            payload_dict: Optional dictionary of parameters
            raw_json: Return raw JSON response if True
            **kwargs: Additional parameters as keyword arguments

        Returns:
            Dictionary containing API response

        Example:
            >>> fgt.api.monitor.network.debug_flow.stop.post()
        """
        data = payload_dict.copy() if payload_dict else {}
        data.update(kwargs)
        return self._client.post(
            "monitor",
            "/network/debug-flow/stop",
            data=data
        )


class DebugFlow:
    """DebugFlow operations."""

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize DebugFlow endpoint.

        Args:
            client: HTTPClient instance for API communication
        """
        self._client = client

        # Initialize nested resources
        self.start = Start(client)
        self.stop = Stop(client)
