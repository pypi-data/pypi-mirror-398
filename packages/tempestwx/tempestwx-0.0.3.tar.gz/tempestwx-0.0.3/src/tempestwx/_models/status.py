"""Status model."""

from __future__ import annotations

from pydantic import ConfigDict, field_validator

from ._serializer import Model


class Status(Model):
    status_code: int | None = None  # int32
    status_message: str | None = None  # string

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )

    @field_validator("status_message")
    @classmethod
    def _empty_str_to_none(cls, v: str | None) -> str | None:
        """Convert empty status messages to None.

        Args:
            v: The status message value.

        Returns:
            None if the message is empty or whitespace-only, otherwise the message.
        """
        if v is not None and v.strip() == "":
            return None
        return v


__all__ = ["Status"]
