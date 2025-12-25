# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, NamedTuple, Optional, Type, TypeVar

import pydantic
from pydantic import ConfigDict, Field, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated


class _dtype(NamedTuple):
    float32: str = "float32"
    float64: str = "float64"
    int8: str = "int8"
    int16: str = "int16"
    int32: str = "int32"
    int64: str = "int64"
    uint8: str = "uint8"
    uint16: str = "uint16"
    uint32: str = "uint32"
    uint64: str = "uint64"


DTYPE = _dtype()


def float32_max() -> float:
    return 3.4028235e38


def float64_max() -> float:
    return 1.7976931348623157e308


def int8_max() -> int:
    return 127


def int8_min() -> int:
    return -128


def int16_max() -> int:
    return 32767


def int16_min() -> int:
    return -32768


def int32_max() -> int:
    return 2147483647


def int32_min() -> int:
    return -2147483648


def int64_max() -> int:
    return 9223372036854775807


def int64_min() -> int:
    return -9223372036854775808


def uint8_max() -> int:
    return 255


def uint8_min() -> int:
    return 0


def uint16_max() -> int:
    return 65535


def uint16_min() -> int:
    return 0


def uint32_max() -> int:
    return 4294967295


def uint32_min() -> int:
    return 0


def uint64_max() -> int:
    return 18446744073709551615


def uint64_min() -> int:
    return 0


# ----------------------------------------------------------------------------
# Type annotation classes


_NumT = TypeVar("_NumT")
_ConstrainedNumT = TypeVar("_ConstrainedNumT")


class DType:
    """Base class for pydantic custom types that have an Arrow .dtype."""

    @classmethod
    # TODO[pydantic]: We couldn't refactor `__modify_schema__`, please create the `__get_pydantic_json_schema__` manually.
    # Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ):
        """Custom JSON schema generation for DType."""
        json_schema = handler(_core_schema)
        dtype = getattr(cls, "dtype", None)
        if dtype is None:
            raise ValueError("subclasses must set cls.dtype")
        json_schema["dyff.io/dtype"] = dtype
        return json_schema


def constrained_type(
    _name: str, _dtype: str, base_type: type, **field_constraints: Any
) -> Type:
    float_annotated_type = Annotated[
        base_type,  # type: ignore [valid-type]
        Field(**field_constraints, json_schema_extra={"dyff.io/dtype": _dtype}),
    ]

    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        if issubclass(base_type, float):
            schema: CoreSchema = core_schema.float_schema(**field_constraints)
        elif issubclass(base_type, int):
            schema = core_schema.int_schema(**field_constraints)
        else:
            raise TypeError(f"Unsupported base_type: {base_type}")
        return core_schema.no_info_after_validator_function(cls.val_type, schema)

    namespace = {
        "val_type": float_annotated_type,
        "name": _name,
        "__get_pydantic_core_schema__": classmethod(__get_pydantic_core_schema__),
        "dtype": _dtype,
        "description": f"A {base_type.__name__} with constraints {field_constraints}",
    }
    return type(_name, (base_type,), namespace)


def float32(
    *,
    strict: bool = False,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    allow_inf_nan: Optional[bool] = None,
) -> Type[float]:
    """Return a type annotation for a float32 field in a pydantic model.

    Note that any keyword arguments *must* be specified here, even if they
    can also be specified in ``pydantic.Field()``. The corresponding keyword
    arguments in ``pydantic.Field()`` will have *no effect*.

    Usage::

        class M(pydantic.BaseModel):
            # Notice how "lt" is specified in the type annotation, not Field()
            x: float32(lt=42) = pydantic.Field(description="some field")
    """
    namespace = dict(
        strict=strict,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
    )
    return constrained_type("Float32Value", DTYPE.float32, float, **namespace)


def float64(
    *,
    strict: bool = False,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    allow_inf_nan: Optional[bool] = None,
) -> Type[float]:
    """Return a type annotation for a float64 field in a pydantic model.

    Note that any keyword arguments *must* be specified here, even if they
    can also be specified in ``pydantic.Field()``. The corresponding keyword
    arguments in ``pydantic.Field()`` will have *no effect*.

    Usage::

        class M(pydantic.BaseModel):
            # Notice how "lt" is specified in the type annotation, not Field()
            x: float64(lt=42) = pydantic.Field(description="some field")
    """
    namespace = dict(
        strict=strict,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
    )
    return constrained_type("Float64Value", DTYPE.float64, float, **namespace)


def int8(
    *,
    strict: bool = False,
    gt: Optional[int] = None,
    ge: Optional[int] = None,
    lt: Optional[int] = None,
    le: Optional[int] = None,
    multiple_of: Optional[int] = None,
) -> Type[int]:
    """Return a type annotation for an int8 field in a pydantic model.

    Note that any keyword arguments *must* be specified here, even if they
    can also be specified in ``pydantic.Field()``. The corresponding keyword
    arguments in ``pydantic.Field()`` will have *no effect*.

    Usage::

        class M(pydantic.BaseModel):
            # Notice how "lt" is specified in the type annotation, not Field()
            x: int8(lt=42) = pydantic.Field(description="some field")
    """
    namespace = dict(strict=strict, gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of)
    return constrained_type("Int8Value", DTYPE.int8, int, **namespace)


def int16(
    *,
    strict: bool = False,
    gt: Optional[int] = None,
    ge: Optional[int] = None,
    lt: Optional[int] = None,
    le: Optional[int] = None,
    multiple_of: Optional[int] = None,
) -> Type[int]:
    """Return a type annotation for an int16 field in a pydantic model.

    Note that any keyword arguments *must* be specified here, even if they
    can also be specified in ``pydantic.Field()``. The corresponding keyword
    arguments in ``pydantic.Field()`` will have *no effect*.

    Usage::

        class M(pydantic.BaseModel):
            # Notice how "lt" is specified in the type annotation, not Field()
            x: int16(lt=42) = pydantic.Field(description="some field")
    """
    namespace = dict(strict=strict, gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of)
    return constrained_type("Int16Value", DTYPE.int16, int, **namespace)


def int32(
    *,
    strict: bool = False,
    gt: Optional[int] = None,
    ge: Optional[int] = None,
    lt: Optional[int] = None,
    le: Optional[int] = None,
    multiple_of: Optional[int] = None,
) -> Type[int]:
    """Return a type annotation for an int32 field in a pydantic model.

    Note that any keyword arguments *must* be specified here, even if they
    can also be specified in ``pydantic.Field()``. The corresponding keyword
    arguments in ``pydantic.Field()`` will have *no effect*.

    Usage::

        class M(pydantic.BaseModel):
            # Notice how "lt" is specified in the type annotation, not Field()
            x: int32(lt=42) = pydantic.Field(description="some field")
    """
    namespace = dict(strict=strict, gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of)
    return constrained_type("Int32Value", DTYPE.int32, int, **namespace)


def int64(
    *,
    strict: bool = False,
    gt: Optional[int] = None,
    ge: Optional[int] = None,
    lt: Optional[int] = None,
    le: Optional[int] = None,
    multiple_of: Optional[int] = None,
) -> Type[int]:
    """Return a type annotation for an int64 field in a pydantic model.

    Note that any keyword arguments *must* be specified here, even if they
    can also be specified in ``pydantic.Field()``. The corresponding keyword
    arguments in ``pydantic.Field()`` will have *no effect*.

    Usage::

        class M(pydantic.BaseModel):
            # Notice how "lt" is specified in the type annotation, not Field()
            x: int64(lt=42) = pydantic.Field(description="some field")
    """
    namespace = dict(strict=strict, gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of)
    return constrained_type("Int64Value", DTYPE.int64, int, **namespace)


def uint8(
    *,
    strict: bool = False,
    gt: Optional[int] = None,
    ge: Optional[int] = None,
    lt: Optional[int] = None,
    le: Optional[int] = None,
    multiple_of: Optional[int] = None,
) -> Type[int]:
    """Return a type annotation for a uint8 field in a pydantic model.

    Note that any keyword arguments *must* be specified here, even if they
    can also be specified in ``pydantic.Field()``. The corresponding keyword
    arguments in ``pydantic.Field()`` will have *no effect*.

    Usage::

        class M(pydantic.BaseModel):
            # Notice how "lt" is specified in the type annotation, not Field()
            x: uint8(lt=42) = pydantic.Field(description="some field")
    """
    namespace = dict(strict=strict, gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of)
    return constrained_type("UInt8Value", DTYPE.uint8, int, **namespace)


def uint16(
    *,
    strict: bool = False,
    gt: Optional[int] = None,
    ge: Optional[int] = None,
    lt: Optional[int] = None,
    le: Optional[int] = None,
    multiple_of: Optional[int] = None,
) -> Type[int]:
    """Return a type annotation for a uint16 field in a pydantic model.

    Note that any keyword arguments *must* be specified here, even if they
    can also be specified in ``pydantic.Field()``. The corresponding keyword
    arguments in ``pydantic.Field()`` will have *no effect*.

    Usage::

        class M(pydantic.BaseModel):
            # Notice how "lt" is specified in the type annotation, not Field()
            x: uint16(lt=42) = pydantic.Field(description="some field")
    """
    namespace = dict(strict=strict, gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of)
    return constrained_type("UInt16Value", DTYPE.uint16, int, **namespace)


def uint32(
    *,
    strict: bool = False,
    gt: Optional[int] = None,
    ge: Optional[int] = None,
    lt: Optional[int] = None,
    le: Optional[int] = None,
    multiple_of: Optional[int] = None,
) -> Type[int]:
    """Return a type annotation for a uint32 field in a pydantic model.

    Note that any keyword arguments *must* be specified here, even if they
    can also be specified in ``pydantic.Field()``. The corresponding keyword
    arguments in ``pydantic.Field()`` will have *no effect*.

    Usage::

        class M(pydantic.BaseModel):
            # Notice how "lt" is specified in the type annotation, not Field()
            x: uint32(lt=42) = pydantic.Field(description="some field")
    """
    namespace = dict(strict=strict, gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of)
    return constrained_type("UInt32Value", DTYPE.uint32, int, **namespace)


def uint64(
    *,
    strict: bool = False,
    gt: Optional[int] = None,
    ge: Optional[int] = None,
    lt: Optional[int] = None,
    le: Optional[int] = None,
    multiple_of: Optional[int] = None,
) -> Type[int]:
    """Return a type annotation for a uint64 field in a pydantic model.

    Note that any keyword arguments *must* be specified here, even if they
    can also be specified in ``pydantic.Field()``. The corresponding keyword
    arguments in ``pydantic.Field()`` will have *no effect*.

    Usage::

        class M(pydantic.BaseModel):
            # Notice how "lt" is specified in the type annotation, not Field()
            x: uint64(lt=42) = pydantic.Field(description="some field")
    """
    namespace = dict(strict=strict, gt=gt, ge=ge, lt=lt, le=le, multiple_of=multiple_of)
    return constrained_type("UInt64Value", DTYPE.uint64, int, **namespace)


_ListElementT = TypeVar("_ListElementT")


def list_(
    item_type: type[_ListElementT], *, list_size: Optional[int] = None
) -> type[list]:
    if list_size is None:
        return Annotated[list[item_type], Field()]  # type: ignore [return-value, valid-type]
    else:
        if list_size <= 0:
            raise ValueError(f"list_size {list_size} must be > 0")
        return Annotated[list[item_type], Field(min_length=list_size, max_length=list_size)]  # type: ignore [return-value, valid-type]


# mypy gets confused because 'dict' is the name of a method in DyffBaseModel
_ModelAsDict = dict[str, Any]


class DyffBaseModel(pydantic.BaseModel):
    """This must be the base class for *all pydantic models* in the Dyff schema.

    Overrides serialization functions to serialize by alias, so that "round-trip"
    serialization is the default for fields with aliases. We prefer aliases because we
    can 1) use _underscore_names_ as reserved names in our data schema, and 2) allow
    Python reserved words like 'bytes' as field names.
    """

    model_config = ConfigDict(extra="forbid")

    # TODO: (DYFF-223) I think that exclude_unset=True should be the default
    # for all schema objects, but I'm unsure of the consequences of making
    # this change and we'll defer it until v1.
    def dict(
        self, *, by_alias: bool = True, exclude_none: bool = True, **kwargs
    ) -> _ModelAsDict:
        return self.model_dump(by_alias=by_alias, exclude_none=exclude_none, **kwargs)

    def json(
        self, *, by_alias: bool = True, exclude_none: bool = True, **kwargs
    ) -> str:
        return self.model_dump_json(
            by_alias=by_alias, exclude_none=exclude_none, **kwargs
        )

    def model_dump(  # type: ignore [override]
        self, *, by_alias: bool = True, exclude_none: bool = True, **kwargs
    ) -> _ModelAsDict:
        return super().model_dump(
            by_alias=by_alias, exclude_none=exclude_none, **kwargs
        )

    def model_dump_json(  # type: ignore [override]
        self, *, by_alias: bool = True, exclude_none: bool = True, **kwargs
    ) -> str:
        return super().model_dump_json(
            by_alias=by_alias, exclude_none=exclude_none, **kwargs
        )


# Note: I *really* wanted to require datetimes to have timezones, like in
# DyffRequestDefaultValidators, but some existing objects in the Auth database
# don't have timezones set currently for historical reasons. It's actually
# better if all datetimes in the system are UTC, so that their JSON
# representations (i.e., isoformat strings) are well-ordered.
class DyffSchemaBaseModel(DyffBaseModel):
    """This should be the base class for *almost all* non-request models in the Dyff
    schema. Models that do not inherit from this class *must* still inherit from
    DyffBaseModel.

    Adds a root validator to ensure that all datetime fields are represented in the UTC
    timezone. This is necessary to avoid errors when comparing "naive" and "aware"
    datetimes. Using the UTC timezone everywhere ensures that JSON representations of
    datetimes are well-ordered.
    """

    @pydantic.model_validator(mode="after")
    def _ensure_datetime_timezone_utc(self):
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, datetime):
                if field_value.tzinfo is None:
                    # Set UTC timezone for naive datetime
                    setattr(self, field_name, field_value.replace(tzinfo=timezone.utc))
                elif field_value.tzinfo != timezone.utc:
                    # Convert to UTC timezone
                    setattr(self, field_name, field_value.astimezone(timezone.utc))
        return self


class JsonMergePatchSemantics(DyffSchemaBaseModel):
    """Explicit None values will be output as json 'null', and fields that are not set
    explicitly are not output.

    In JSON Merge Patch terms, None means "delete this field", and not setting a value
    means "leave this field unchanged".
    """

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        """This method runs automatically when ANY class inherits from
        JsonMergePatchSemantics."""
        super().__pydantic_init_subclass__(**kwargs)

        current_config = getattr(cls, "model_config", {})
        if hasattr(current_config, "copy"):
            current_config = current_config.copy()
        else:
            current_config = dict(current_config) if current_config else {}

        existing_json_schema_extra = current_config.get("json_schema_extra", None)

        def remove_defaults_from_schema(schema: dict, model_type: type) -> None:
            if existing_json_schema_extra:
                if callable(existing_json_schema_extra):
                    existing_json_schema_extra(schema, model_type)
                elif isinstance(existing_json_schema_extra, dict):
                    schema.update(existing_json_schema_extra)

            properties = schema.get("properties", {})
            for field_name, field_schema in properties.items():
                if isinstance(field_schema, dict) and "default" in field_schema:
                    field_schema.pop("default")

        current_config["json_schema_extra"] = remove_defaults_from_schema
        cls.model_config = current_config

    def dict(  # type: ignore [override]
        self,
        *,
        by_alias: bool = True,
        exclude_unset=True,
        exclude_none=False,
        **kwargs: Mapping[str, Any],
    ) -> _ModelAsDict:
        return self.model_dump(
            by_alias=by_alias,
            exclude_unset=True,
            exclude_none=False,
            **kwargs,
        )

    def json(  # type: ignore [override]
        self,
        *,
        by_alias: bool = True,
        exclude_unset: bool = True,
        exclude_none: bool = False,
        **kwargs: Mapping[str, Any],
    ) -> str:
        return self.model_dump_json(
            by_alias=by_alias,
            exclude_unset=True,
            exclude_none=False,
            **kwargs,
        )

    def model_dump(  # type: ignore [override]
        self,
        *,
        by_alias: bool = True,
        exclude_unset: bool = True,
        exclude_none: bool = False,
        **kwargs: Mapping[str, Any],
    ) -> _ModelAsDict:
        return super().model_dump(
            by_alias=by_alias,
            exclude_unset=True,
            exclude_none=False,
            **kwargs,
        )

    def model_dump_json(  # type: ignore [override]
        self,
        *,
        by_alias: bool = True,
        exclude_unset: bool = True,
        exclude_none: bool = False,
        **kwargs: Mapping[str, Any],
    ) -> str:
        return super().model_dump_json(
            by_alias=by_alias,
            exclude_unset=True,
            exclude_none=False,
            **kwargs,
        )


__all__ = [
    "DTYPE",
    "DType",
    "DyffBaseModel",
    "DyffSchemaBaseModel",
    "JsonMergePatchSemantics",
    "float32",
    "float32_max",
    "float64",
    "float64_max",
    "int8",
    "int8_max",
    "int8_min",
    "int16",
    "int16_max",
    "int16_min",
    "int32",
    "int32_max",
    "int32_min",
    "int64",
    "int64_max",
    "int64_min",
    "list_",
    "uint8",
    "uint8_max",
    "uint8_min",
    "uint16",
    "uint16_max",
    "uint16_min",
    "uint32",
    "uint32_max",
    "uint32_min",
    "uint64",
    "uint64_max",
    "uint64_min",
]
