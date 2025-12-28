"""Lightweight processors used by the client layer.

This module provides small, composable helpers for shaping API response data:

- `pass_through`: returns a value unchanged (useful as a default processor).
- `model_instance`: factory that builds a callable to convert a mapping into
    an instance of a provided `Model` subclass, returning `None` for `None`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, TypeVar

from tempestwx._models import Model

T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=Model)


def pass_through(value: T) -> T:
    """Return the input value unchanged.

    This is an identity function used as a no-op processor when you want
    to pass response data through without transformation. The generic type
    parameter ``T`` ensures the output type matches the input type.

    Args:
        value: Any value to return unchanged.

    Returns:
        The same value that was passed in.

    Example:
        >>> pass_through({"key": "value"})
        {"key": "value"}
        >>> pass_through(42)
        42
    """
    return value


def model_instance(
    type_: type[ModelT],
) -> Callable[[Mapping[str, Any] | None], ModelT | None]:
    """Create a function that instantiates a Pydantic model from a mapping.

    This factory function returns a callable that converts a dictionary or
    mapping into an instance of the specified Pydantic model class. It's
    designed to work with the decorator chain in API endpoint methods.

    The generic type parameter ``ModelT`` is bounded by ``Model``, meaning
    it must be a Pydantic model subclass. This preserves type information
    so the returned callable is properly typed.

    Args:
        type_: A Pydantic model class (not an instance) to instantiate.

    Returns:
        A callable that takes an optional mapping and returns an optional
        model instance. If the input is ``None``, returns ``None``. Otherwise,
        unpacks the mapping as keyword arguments to construct the model.

    Example:
        >>> from tempestwx._models.station_set import StationSet
        >>> builder = model_instance(StationSet)
        >>> data = {"stations": [...]}
        >>> result = builder(data)  # Returns StationSet instance
        >>> result = builder(None)  # Returns None
    """
    return lambda data: type_(**data) if data is not None else None
