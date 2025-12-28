"""Request and error handling decorators.

Provides decorators used to wrap API endpoint methods with:
- Automatic HTTP request lifecycle management (``make_request``)
- Standardized error handling and transformation (``handle_errors``)

Internal to the SDK; endpoint methods in ``api/`` use these decorators.
"""

from .error_handler import handle_errors
from .request_handler import make_request

__all__ = [
    "handle_errors",
    "make_request",
]
