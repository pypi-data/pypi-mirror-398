"""Access token abstractions for authentication.

This module provides the token handling infrastructure for authenticating
API requests. Currently supports Personal Access Tokens (PAT). OAuth flows
such as Authorization Code with PKCE are not yet implemented.

Classes:
    AccessToken: Abstract base for token implementations.
    Token: Concrete PAT implementation that extracts and stores bearer tokens.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AccessToken(ABC):
    """Access Token base class."""

    @property
    @abstractmethod
    def access_token(self) -> str:
        """Bearer token."""
        raise NotImplementedError

    def __str__(self) -> str:
        """Return the string representation of the Bearer token."""
        return self.access_token


class Token(AccessToken):
    """Access Token implementation.

    Represents a Personal Access Tokens (PAT).
    OAuth Authorization Code (with PKCE) grant types are not yet supported.
    """

    def __init__(self, token_details: dict[str, Any]) -> None:
        """Initialize a Token from token details.

        Args:
            token_details: Dictionary containing token information. Must include
                an ``"access_token"`` key with the bearer token string.

        Raises:
            KeyError: If ``"access_token"`` key is missing from token_details.
        """
        self._access_token: str = token_details["access_token"]

    def __repr__(self) -> str:
        options = [
            f"access_token={self.access_token!r}",
        ]
        return type(self).__name__ + "(" + ", ".join(options) + ")"

    @property
    def access_token(self) -> str:
        """Bearer token."""
        return self._access_token
