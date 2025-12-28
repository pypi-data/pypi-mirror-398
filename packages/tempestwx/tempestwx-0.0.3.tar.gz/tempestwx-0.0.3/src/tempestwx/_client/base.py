"""Base client class providing core HTTP and configuration functionality.

This module defines ``TempestBase``, the foundational class that all Tempest
API endpoint clients inherit from. It provides:

- Token management and context-based token overrides
- Settings integration (API URI, units, configuration)
- HTTP method builders (_get, _post, _put, _delete)
- Request URL construction and header building
- Parameter validation for enum-based options
- Integration with the transport layer for request execution

The base class is not intended to be instantiated directly. Instead, it serves
as a parent class for endpoint-specific implementations that add decorated
methods for particular API operations.

Internal API:
    This module contains internal implementation details. Users should interact
    with the public ``Tempest`` client class instead.
"""

from __future__ import annotations

from collections.abc import Coroutine
from contextvars import ContextVar
from enum import Enum
from typing import Any, TypeVar

from tempestwx._http import Client, Request, Response, Transport
from tempestwx.settings import Settings
from tempestwx.settings_loader import load_settings

# Type variable for generic enum validation (module-scoped)
_E = TypeVar("_E", bound=Enum)


class TempestBase(Client):
    """Base client with core HTTP and configuration functionality.

    Provides foundational capabilities for all Tempest API endpoint clients:
    - Token management via ContextVar for thread-safe context overrides
    - Settings integration (API URI, default units, token resolution)
    - HTTP request builders for GET, POST, PUT, DELETE operations
    - URL construction and header management
    - Enum parameter validation

    This class is not intended for direct instantiation. It serves as a parent
    for endpoint-specific classes that add decorated API methods.

    Attributes:
        settings: Resolved settings including API URI, units, and token.
        _token: The current access token (may be None).
        _token_cv: ContextVar for thread-safe token context management.
    """

    _token_cv: ContextVar[str] = ContextVar("_token_cv")

    def __init__(
        self,
        token: str | None = None,
        transport: Transport | None = None,
        asynchronous: bool | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize the base client with authentication and configuration.

        Args:
            token: Access token for API authentication. If provided, overrides
                the token from settings or environment.
            transport: Custom HTTP transport implementation. If None, a default
                transport will be created based on the asynchronous flag.
            asynchronous: Whether to use async/await patterns. Determines which
                transport implementation to use.
            settings: Pre-constructed Settings object. If None, loads settings
                from environment, .env file, and config.json via load_settings().
        """
        super().__init__(transport, asynchronous)
        base_settings = settings or load_settings()
        self.settings = (
            base_settings.with_overrides(token=token)
            if token is not None
            else base_settings
        )
        self._token = self.settings.token

    @property
    def token(self) -> str:
        """Get the current access token, respecting context overrides.

        Returns the token from the current ContextVar context if set (via
        token_as() context manager), otherwise returns the base token from
        settings.

        Returns:
            The active bearer token string.
        """
        # ContextVar.get() requires non-None default, so use empty string as fallback
        # and coalesce with self._token which may also be None
        return self._token_cv.get(self._token or "")

    @token.setter
    def token(self, value: str) -> None:
        """Set the access token, handling both base and context values.

        If a context token is already set (via ContextVar), updates the context
        token. Otherwise, updates the base token.

        Args:
            value: The new bearer token string.
        """
        try:
            self._token_cv.get()
        except LookupError:
            self._token = value
        else:
            self._token_cv.set(value)

    def __repr__(self) -> str:
        options = [
            f"token={self.token!r}",
            f"transport={self.transport!r}",
        ]
        return type(self).__name__ + "(" + ", ".join(options) + ")"

    def _create_headers(self, content_type: str = "application/json") -> dict[str, str]:
        """Build HTTP headers for API requests.

        Creates standard headers including Authorization bearer token and
        Content-Type.

        Args:
            content_type: The MIME type for the Content-Type header.
                Defaults to "application/json".

        Returns:
            Dictionary of HTTP headers ready for request.
        """
        return {
            "Authorization": f"Bearer {self.token!s}",
            "Content-Type": content_type,
        }

    @staticmethod
    def _validate_enum_param(
        param_name: str,
        value: _E | str | int,
        enum_class: type[_E],
    ) -> _E:
        """Validate and convert a parameter to its enum type.

        Args:
            param_name: Name of the parameter (for error messages).
            value: The value to validate (enum instance or literal such as
                string or integer).
            enum_class: The enum class to validate against.

        Returns:
            The validated enum instance.

        Raises:
            ValueError: If the value is not a valid member of the enum.
        """
        if isinstance(value, enum_class):
            return value

        # Attempt to coerce common literal types (e.g., str, int) to the enum
        try:
            return enum_class(value)
        except (ValueError, TypeError):
            valid_values = [e.value for e in enum_class]
            raise ValueError(
                f"Invalid {param_name}: {value!r}. Valid: {valid_values}"
            ) from None

    def send(self, request: Request) -> Response | Coroutine[None, None, Response]:
        """Build request url and headers, and send with underlying transport.

        Exposed to easily send arbitrary requests,
        for custom behavior in some endpoint e.g. for a subclass.
        It may also come in handy if a bugfix or a feature is not implemented
        in a timely manner, or in debugging related to the client or Web API.
        """
        request.url = self._build_url(request.url)
        headers = self._create_headers()
        if request.headers is not None:
            headers.update(request.headers)
        request.headers = headers
        return self.transport.send(request)

    def _build_url(self, url: str) -> str:
        """Build complete URL by prepending API base if needed.

        If the URL doesn't start with "https", prepends the configured API
        base URI from settings. This allows endpoint methods to use relative
        paths while supporting absolute URLs when needed.

        Args:
            url: Either a relative path (e.g., "stations") or absolute URL.

        Returns:
            Complete URL ready for HTTP request.
        """
        if not url.startswith("https"):
            url = self.settings.api_uri_normalized + url.lstrip("/")
        return url

    @staticmethod
    def _parse_url_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
        """Filter None values from query parameters.

        Removes parameters with None values to avoid sending them in the
        query string. Returns None if the filtered dict is empty.

        Args:
            params: Dictionary of query parameters, potentially with None values.

        Returns:
            Filtered parameter dict, or None if empty or all values were None.
        """
        params = params or {}
        return {k: v for k, v in params.items() if v is not None} or None

    @staticmethod
    def _request(
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> tuple[Request, tuple[()]]:
        """Build a Request object from method, URL, payload, and parameters.

        Constructs a Request dataclass instance with filtered parameters (None
        values removed). Returns the request along with an empty tuple that
        serves as extra data for the decorator chain.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            url: Request URL (relative or absolute).
            payload: Optional JSON body data.
            params: Optional query string parameters.

        Returns:
            Tuple of (Request object, empty tuple for decorator chain).
        """
        return (
            Request(
                method=method,
                url=url,
                params=TempestBase._parse_url_params(params),
                json=payload,
            ),
            (),
        )

    def _get(self, url: str, payload: dict | None = None, **params):  # type: ignore[type-arg, no-untyped-def]
        req, extra = self._request("GET", url, payload=payload, params=params)
        req.url = self._build_url(req.url)
        return req, extra

    def _post(self, url: str, payload: dict | None = None, **params):  # type: ignore[type-arg, no-untyped-def]
        req, extra = self._request("POST", url, payload=payload, params=params)
        req.url = self._build_url(req.url)
        return req, extra

    def _delete(self, url: str, payload: dict | None = None, **params):  # type: ignore[type-arg, no-untyped-def]
        req, extra = self._request("DELETE", url, payload=payload, params=params)
        req.url = self._build_url(req.url)
        return req, extra

    def _put(self, url: str, payload: dict | None = None, **params):  # type: ignore[type-arg, no-untyped-def]
        req, extra = self._request("PUT", url, payload=payload, params=params)
        req.url = self._build_url(req.url)
        return req, extra
