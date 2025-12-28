"""Request decorator for API endpoint methods.

This module provides the ``make_request`` decorator that transforms endpoint
methods into full HTTP request/response handlers. It integrates error handling
and response processing into a single decorator that can be applied to API
endpoint methods.

The decorator works with the ``send_and_process`` transport layer to execute
requests and apply post-processing functions (like model instantiation) to
the response data.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tempestwx._http import Request, Response
from tempestwx._http.client import send_and_process as _send_and_process

from .error_handler import handle_errors


def make_request(post_func: Callable[[Any], Any]) -> Callable[..., Any]:
    """Decorate an endpoint method to execute HTTP requests with processing.

    This decorator transforms an endpoint method that returns a request tuple
    into a full HTTP handler. It wraps the method to:

    1. Execute the HTTP request via the transport layer
    2. Check for errors and raise exceptions if needed
    3. Apply a post-processing function to the response content

    The post-processing function is typically used to deserialize JSON
    response data into Pydantic model instances.

    Args:
        post_func: A callable that processes the response content. Takes
            the parsed JSON content (or None) and returns a transformed
            result (e.g., a Pydantic model instance). Commonly created
            via ``model_instance()`` or ``pass_through()``.

    Returns:
        A decorator function that can be applied to endpoint methods.
        The decorated method will have the signature of the original
        method but will execute the full request/response cycle.

    Example:
        >>> @make_request(model_instance(StationSet))
        ... def stations(self) -> StationSet:
        ...     return self._get("stations")
    """

    def parse_response(request: Request, response: Response) -> Any:
        handle_errors(request, response)
        return post_func(response.content)

    return _send_and_process(parse_response)
