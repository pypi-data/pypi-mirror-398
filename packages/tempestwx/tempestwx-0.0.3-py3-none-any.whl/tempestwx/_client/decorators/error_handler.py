"""Error handling utilities for API responses.

This module provides functions to parse error messages from API responses
and raise appropriate exceptions based on HTTP status codes. It integrates
with the decorator chain to handle error responses before processing.
"""

from typing import cast

from httpx import codes

from tempestwx._http import Request, Response
from tempestwx._http.error import get_error

error_format = "Error in {url}: {code}: {msg}"


def parse_error_message(response: Response) -> str:
    """Extract error status message from response content.

    Attempts to retrieve a descriptive error message from the response's
    JSON content. Falls back to a generic status attribute if the content
    is None or doesn't contain the expected structure.

    Args:
        response: The HTTP response object containing error information.

    Returns:
        A string describing the error. Either the status_message from the
        response content, or a fallback status string.
    """
    status = getattr(response, "status", "")
    if response.content is None:
        return status
    error = response.content["status"]
    return cast(str, error.get("status_message", status))


def handle_errors(request: Request, response: Response) -> None:
    """Parse response and raise appropriate exception if an error occurred.

    Checks the response status code and raises a specific exception class
    if it indicates an error (4xx or 5xx). The exception includes the
    request URL, status code, and a descriptive error message.

    Args:
        request: The original HTTP request that was sent.
        response: The HTTP response received from the API.

    Raises:
        HTTPError subclass: Appropriate exception based on status code
            (e.g., BadRequestError, UnauthorisedError, NotFoundError).
    """
    if codes.is_error(response.status_code):
        error_str = error_format.format(
            url=response.url,
            code=response.status_code,
            msg=parse_error_message(response),
        )
        error_cls = get_error(response.status_code)
        raise error_cls(error_str, request=request, response=response)
