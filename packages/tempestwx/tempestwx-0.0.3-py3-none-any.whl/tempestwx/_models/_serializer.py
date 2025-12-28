"""Serialization utilities for Tempest API models.

Provides base classes and utilities for Pydantic models:
- ``StrEnum`` - case-insensitive string enum with Pydantic validation
- ``StrEnumMeta`` - metaclass enabling case-insensitive enum member lookup
- ``Model`` - base response model with unknown attribute warnings
- ``UnknownModelAttributeWarning`` - warning for undocumented API fields

These utilities ensure robust handling of API responses while warning about
undocumented fields that may appear in future API versions.
"""

from enum import Enum, EnumMeta
from warnings import warn

from pydantic import AliasChoices, AliasPath, BaseModel
from pydantic_core import core_schema


class StrEnumMeta(EnumMeta):
    """Metaclass for StrEnum that provides case-insensitive get.

    This does not change values.
    """

    def __new__(mcs, cls, bases, classdict, **kwds):  # type: ignore[no-untyped-def]
        """Override `__new__` to make all keys lowercase.

        Args:
            mcs: The metaclass.
            cls: The class name.
            bases: Base classes.
            classdict: Class dictionary.
            **kwds: Additional keyword arguments.

        Returns:
            The enum class with lowercase member map keys.
        """
        enum_class = super().__new__(mcs, cls, bases, classdict, **kwds)
        copied_member_map = dict(enum_class._member_map_)
        enum_class._member_map_.clear()
        for k, v in copied_member_map.items():
            enum_class._member_map_[k.lower()] = v
        return enum_class

    def __getitem__(cls, name: str):  # type: ignore[no-untyped-def]
        """Get enum member by name (case-insensitive).

        Args:
            name: The enum member name (any case).

        Returns:
            The enum member.
        """
        return super().__getitem__(name.lower())


class StrEnum(str, Enum, metaclass=StrEnumMeta):
    """Convert enumeration members to strings using their name.

    Ignores case when getting items. This does not change values.

    Works with Pydantic strict mode by providing custom validation.
    """

    @classmethod
    def _missing_(cls, value):  # type: ignore[no-untyped-def]
        """Handle missing enum values with case-insensitive lookup.

        Args:
            value: The value to look up.

        Returns:
            The enum member matching the value (case-insensitive).
        """
        return cls[value.lower()]

    def __str__(self) -> str:
        return self.name

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):  # type: ignore[no-untyped-def]
        """Provide Pydantic schema for string-to-enum coercion.

        Works with strict mode by accepting both enum instances and strings.

        Args:
            source_type: The source type being validated.
            handler: Pydantic's schema generation handler.

        Returns:
            A Pydantic core schema for validation.
        """
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    core_schema.str_schema(),
                ]
            ),
        )

    @classmethod
    def _validate(cls, v):  # type: ignore[no-untyped-def]
        """Convert string values to enum instances.

        Args:
            v: The value to validate (enum instance or string).

        Returns:
            The validated enum instance.
        """
        if isinstance(v, cls):
            return v
        if isinstance(v, str):
            try:
                return cls(v)
            except ValueError:
                # Try case-insensitive match using _missing_
                return cls._missing_(v)  # type: ignore[no-untyped-call]
        return v


class Model(BaseModel):
    """Response model base."""

    def __init__(self, **data) -> None:  # type: ignore[no-untyped-def]
        """Initialize model and warn about unknown attributes.

        Args:
            **data: Field values for the model.

        Warns:
            UnknownModelAttributeWarning: When response contains undocumented fields.
        """
        super().__init__(**data)

        # Build a set of known keys that includes both field names and any
        # accepted aliases used during validation (e.g., Field(alias="type")).
        known_keys = set(self.__dict__.keys())

        # Use class-level __pydantic_fields__ to avoid deprecation of
        # model_fields
        fields = type(self).__pydantic_fields__  # dict[str, FieldInfo]
        for field_info in fields.values():
            # Primary alias
            alias = getattr(field_info, "alias", None)
            if isinstance(alias, str):
                known_keys.add(alias)

            # validation_alias may be a string, AliasChoices, or AliasPath
            v_alias = getattr(field_info, "validation_alias", None)
            if v_alias is None:
                pass
            elif isinstance(v_alias, str):
                known_keys.add(v_alias)
            # Handle AliasChoices
            elif isinstance(v_alias, AliasChoices):
                for c in v_alias.choices:
                    if isinstance(c, str):
                        known_keys.add(c)
                    elif (
                        isinstance(c, AliasPath)
                        and c.path
                        and isinstance(c.path, (list, tuple))
                        and isinstance(c.path[0], str)
                    ):
                        known_keys.add(c.path[0])
            # Handle AliasPath (take top-level key if present)
            elif (
                isinstance(v_alias, AliasPath)
                and v_alias.path
                and isinstance(v_alias.path, (list, tuple))
                and isinstance(v_alias.path[0], str)
            ):
                known_keys.add(v_alias.path[0])

        unknowns = set(data.keys()) - known_keys
        cls_name = self.__class__.__name__
        for arg in unknowns:
            msg = (
                f"{cls_name} contains unknown attribute: `{arg}`, "
                "which was discarded. This warning may be safely ignored. "
                "Please consider upgrading."
            )
            warn(msg, UnknownModelAttributeWarning, stacklevel=5)


class UnknownModelAttributeWarning(RuntimeWarning):
    """The response model contains an unknown attribute."""
