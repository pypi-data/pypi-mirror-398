"""HTTP error hierarchy for API exceptions.

This module defines a comprehensive exception hierarchy for HTTP errors returned
by the Tempest Weather API. The hierarchy mirrors HTTP status code categories:

- HTTPError: Base exception for all HTTP errors
  - ClientError (4xx): Errors caused by invalid client requests
    - BadRequestError (400)
    - UnauthorisedError (401)
    - ForbiddenError (403)
    - NotFoundError (404)
    - TooManyRequestsError (429)
  - ServerError (5xx): Errors caused by server issues
    - InternalServerError (500)
    - BadGatewayError (502)
    - ServiceUnavailableError (503)

Each exception includes the original request and response for debugging.
The get_error() function maps status codes to appropriate exception classes.
"""

from httpx import codes

from .base import Request, Response


class HTTPError(Exception):
    """Base error for all web status errors.

    Attributes:
    ----------
    request
        request that led to the error
    response
        response from the web server
    """

    def __init__(self, message: str, request: Request, response: Response) -> None:
        super().__init__(message)
        self.request = request
        self.response = response


class ClientError(HTTPError):
    """4xx - Base client error."""


class ServerError(HTTPError):
    """5xx - Base server error."""


class BadRequestError(ClientError):
    """400 - Bad request.

    The request could not be understood by the server due to malformed syntax.
    """


class UnauthorisedError(ClientError):
    """401 - Unauthorised.

    The request requires user authentication or,
    if the request included authorization credentials,
    authorization has been refused for those credentials.

    The scopes associated with the call are attached to this class.
    """

    scope: str
    required_scope: str
    optional_scope: str


class ForbiddenError(ClientError):
    """403 - Forbidden.

    The server understood the request, but is refusing to fulfill it.
    """


class NotFoundError(ClientError):
    """404 - Not found.

    The requested resource could not be found.
    This error can be due to a temporary or permanent condition.
    """


class TooManyRequestsError(ClientError):
    """429 - Too many requests.

    Rate limiting has been applied.
    """


class InternalServerError(ServerError):
    """500 - Internal server error.

    You should never receive this error ;).
    """


class BadGatewayError(ClientError):
    """502 - Bad gateway.

    The server was acting as a gateway or proxy and received
    an invalid response from the upstream server.
    """


class ServiceUnavailableError(ClientError):
    """503 - Service unavailable.

    The server is currently unable to handle the request due to a temporary
    condition which will be alleviated after some delay.
    You can choose to resend the request again.
    """


errors = {
    400: BadRequestError,
    401: UnauthorisedError,
    403: ForbiddenError,
    404: NotFoundError,
    429: TooManyRequestsError,
    500: InternalServerError,
    502: BadGatewayError,
    503: ServiceUnavailableError,
}


def get_error(code: int) -> type[HTTPError]:
    """Get exception class based on HTTP status code.

    Maps status codes to specific exception classes. Falls back to generic
    ClientError for unmapped 4xx codes or ServerError for unmapped 5xx codes.

    Args:
        code: HTTP status code (e.g., 400, 401, 500).

    Returns:
        Exception class appropriate for the status code.

    Example:
        >>> error_cls = get_error(404)
        >>> raise error_cls("Not found", request, response)
    """
    cls = errors.get(code)
    if cls is None:
        cls = ClientError if codes.is_client_error(code) else ServerError
    return cls
