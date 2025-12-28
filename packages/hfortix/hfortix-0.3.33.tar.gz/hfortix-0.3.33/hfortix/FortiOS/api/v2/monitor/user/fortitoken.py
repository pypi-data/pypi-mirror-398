"""
FortiOS MONITOR - Monitor User Fortitoken

Monitoring endpoint for monitor user fortitoken data.

API Endpoints:
    GET    /monitor/user/fortitoken

Example Usage:
    >>> from hfortix.FortiOS import FortiOS
    >>> fgt = FortiOS(host="192.168.1.99", token="your-api-token")
    >>>
    >>> # Get monitoring/log data (read-only)
    >>> data = fgt.api.monitor.user.fortitoken.get()
    >>>
    >>> # With filters and parameters
    >>> data = fgt.api.monitor.user.fortitoken.get(
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


class Activate:
    """
    Activate Operations.

    Provides read-only access for FortiOS activate data.

    Methods:
        get(): Retrieve monitoring/log data (read-only)

    Note:
        This is a read-only endpoint. Configuration changes are not supported.
    """

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize Activate endpoint.

        Args:
            client: HTTPClient instance
        """
        self._client = client

    def post(
        self,
        tokens: list | None = None,
        payload_dict: dict[str, Any] | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Activate a set of FortiTokens by serial number.

        Args:
            tokens: List of FortiToken serial numbers to activate. If omitted,
            all tokens will be used. (optional)
            payload_dict: Optional dictionary of parameters
            raw_json: Return raw JSON response if True
            **kwargs: Additional parameters as keyword arguments

        Returns:
            Dictionary containing API response

        Example:
            >>> fgt.api.monitor.user.fortitoken.activate.post()
        """
        data = payload_dict.copy() if payload_dict else {}
        if tokens is not None:
            data['tokens'] = tokens
        data.update(kwargs)
        return self._client.post(
            "monitor",
            "/user/fortitoken/activate",
            data=data
        )


class ImportMobile:
    """ImportMobile operations."""

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize ImportMobile endpoint.

        Args:
            client: HTTPClient instance
        """
        self._client = client

    def post(
        self,
        code: str | None = None,
        payload_dict: dict[str, Any] | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Import a list of tokens from FortiGuard to the FortiGate unit.

        Args:
            code: Activation code on redemption certificate. (optional)
            payload_dict: Optional dictionary of parameters
            raw_json: Return raw JSON response if True
            **kwargs: Additional parameters as keyword arguments

        Returns:
            Dictionary containing API response

        Example:
            >>> fgt.api.monitor.user.fortitoken.import_mobile.post()
        """
        data = payload_dict.copy() if payload_dict else {}
        if code is not None:
            data['code'] = code
        data.update(kwargs)
        return self._client.post(
            "monitor",
            "/user/fortitoken/import-mobile",
            data=data
        )


class ImportSeed:
    """ImportSeed operations."""

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize ImportSeed endpoint.

        Args:
            client: HTTPClient instance
        """
        self._client = client

    def post(
        self,
        file_content: str | None = None,
        payload_dict: dict[str, Any] | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Import a FortiToken seed file.

        Args:
            file_content: Provided when uploading a file: base64 encoded file
            data. Must not contain whitespace or other invalid base64
            characters. Must be included in HTTP body. (optional)
            payload_dict: Optional dictionary of parameters
            raw_json: Return raw JSON response if True
            **kwargs: Additional parameters as keyword arguments

        Returns:
            Dictionary containing API response

        Example:
            >>> fgt.api.monitor.user.fortitoken.import_seed.post()
        """
        data = payload_dict.copy() if payload_dict else {}
        if file_content is not None:
            data['file_content'] = file_content
        data.update(kwargs)
        return self._client.post(
            "monitor",
            "/user/fortitoken/import-seed",
            data=data
        )


class ImportTrial:
    """ImportTrial operations."""

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize ImportTrial endpoint.

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
        Import trial mobile FortiTokens.

        Args:
            payload_dict: Optional dictionary of parameters
            raw_json: Return raw JSON response if True
            **kwargs: Additional parameters as keyword arguments

        Returns:
            Dictionary containing API response

        Example:
            >>> fgt.api.monitor.user.fortitoken.import_trial.post()
        """
        data = payload_dict.copy() if payload_dict else {}
        data.update(kwargs)
        return self._client.post(
            "monitor",
            "/user/fortitoken/import-trial",
            data=data
        )


class Provision:
    """Provision operations."""

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize Provision endpoint.

        Args:
            client: HTTPClient instance
        """
        self._client = client

    def post(
        self,
        tokens: list | None = None,
        payload_dict: dict[str, Any] | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Provision a set of FortiTokens by serial number.

        Args:
            tokens: List of FortiToken serial numbers to provision. If omitted,
            all tokens will be used. (optional)
            payload_dict: Optional dictionary of parameters
            raw_json: Return raw JSON response if True
            **kwargs: Additional parameters as keyword arguments

        Returns:
            Dictionary containing API response

        Example:
            >>> fgt.api.monitor.user.fortitoken.provision.post()
        """
        data = payload_dict.copy() if payload_dict else {}
        if tokens is not None:
            data['tokens'] = tokens
        data.update(kwargs)
        return self._client.post(
            "monitor",
            "/user/fortitoken/provision",
            data=data
        )


class Refresh:
    """Refresh operations."""

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize Refresh endpoint.

        Args:
            client: HTTPClient instance
        """
        self._client = client

    def post(
        self,
        tokens: list | None = None,
        payload_dict: dict[str, Any] | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Refresh a set of FortiTokens by serial number.

        Args:
            tokens: List of FortiToken serial numbers to refresh. If omitted,
            all tokens will be used. (optional)
            payload_dict: Optional dictionary of parameters
            raw_json: Return raw JSON response if True
            **kwargs: Additional parameters as keyword arguments

        Returns:
            Dictionary containing API response

        Example:
            >>> fgt.api.monitor.user.fortitoken.refresh.post()
        """
        data = payload_dict.copy() if payload_dict else {}
        if tokens is not None:
            data['tokens'] = tokens
        data.update(kwargs)
        return self._client.post(
            "monitor",
            "/user/fortitoken/refresh",
            data=data
        )


class SendActivation:
    """SendActivation operations."""

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize SendActivation endpoint.

        Args:
            client: HTTPClient instance
        """
        self._client = client

    def post(
        self,
        token: str | None = None,
        method: str | None = None,
        email: str | None = None,
        sms_phone: str | None = None,
        payload_dict: dict[str, Any] | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Send a FortiToken activation code to a user via SMS or Email.

        Args:
            token: FortiToken serial number. The token must be assigned to a
            user/admin. (optional)
            method: Method to send activation code [email|sms]. If not set, SMS
            will be attempted first, then email. (optional)
            email: Override email address. (optional)
            sms_phone: Override SMS phone number. SMS provider must be set in
            the assigned user/admin. (optional)
            payload_dict: Optional dictionary of parameters
            raw_json: Return raw JSON response if True
            **kwargs: Additional parameters as keyword arguments

        Returns:
            Dictionary containing API response

        Example:
            >>> fgt.api.monitor.user.fortitoken.send_activation.post()
        """
        data = payload_dict.copy() if payload_dict else {}
        if token is not None:
            data['token'] = token
        if method is not None:
            data['method'] = method
        if email is not None:
            data['email'] = email
        if sms_phone is not None:
            data['sms_phone'] = sms_phone
        data.update(kwargs)
        return self._client.post(
            "monitor",
            "/user/fortitoken/send-activation",
            data=data
        )


class Fortitoken:
    """Fortitoken operations."""

    def __init__(self, client: 'IHTTPClient'):
        """
        Initialize Fortitoken endpoint.

        Args:
            client: HTTPClient instance for API communication
        """
        self._client = client

        # Initialize nested resources
        self.activate = Activate(client)
        self.import_mobile = ImportMobile(client)
        self.import_seed = ImportSeed(client)
        self.import_trial = ImportTrial(client)
        self.provision = Provision(client)
        self.refresh = Refresh(client)
        self.send_activation = SendActivation(client)

    def get(
        self,
        payload_dict: dict[str, Any] | None = None,
        raw_json: bool = False,
        **kwargs: Any,
    ) -> Union[dict[str, Any], Coroutine[Any, Any, dict[str, Any]]]:
        """
        Retrieve a map of FortiTokens and their status.

        Args:
            payload_dict: Optional dictionary of parameters
            raw_json: Return raw JSON response if True
            **kwargs: Additional parameters as keyword arguments

        Returns:
            Dictionary containing API response

        Example:
            >>> fgt.api.monitor.user.fortitoken.get()
        """
        params = payload_dict.copy() if payload_dict else {}
        params.update(kwargs)
        return self._client.get("monitor", "/user/fortitoken", params=params)
