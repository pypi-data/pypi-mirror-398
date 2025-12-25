# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import importlib
from typing import Any, Iterable, Type, TypeVar, Union

import pydantic

from .base import DyffBaseModel, DyffSchemaBaseModel
from .version import SomeSchemaVersion


def _symbol(fully_qualified_name):
    tokens = fully_qualified_name.split(".")
    module_name = ".".join(tokens[:-1])
    member = tokens[-1]
    module = importlib.import_module(module_name)
    return getattr(module, member)


def product_schema(
    schemas: Iterable[Type[DyffSchemaBaseModel]],
) -> Type[DyffSchemaBaseModel]:
    return pydantic.create_model("Product", __base__=tuple(schemas))


# TODO: Should have a way of registering schema names rather than allowing
# arbitrary imports.
def named_data_schema(
    name: str, schema_version: SomeSchemaVersion
) -> Type[DyffSchemaBaseModel]:
    version, revision = schema_version.split(".")
    return _symbol(f"dyff.schema.v{version}.r{revision}.dataset.{name}")


_UpcastTargetT = TypeVar("_UpcastTargetT", bound=DyffBaseModel)
_UpcastSourceT = TypeVar("_UpcastSourceT", bound=DyffBaseModel)


def upcast(
    t: type[_UpcastTargetT], obj: Union[_UpcastSourceT, dict[str, Any]]
) -> _UpcastTargetT:
    """Perform a "structural upcast" on a Pydantic model instance.

    An upcast is possible when the top-level fields of the target type are a subset of
    the top-level fields of the source type, and the data in each source field validates
    against the corresponding target field. In particular, an upcast is possible when
    the source type is a Python subclass of the target type.

    The upcast is "shallow" in the sense that sub-objects must validate as-is. In
    particular, most Dyff schema types do not allow additional properties, so validation
    will fail if a sub-object of the source object has fields that are not present in
    the corresponding sub-object of the target type.
    """
    if not isinstance(obj, dict):
        # Preserve the unset status
        obj = obj.dict(exclude_unset=True)
    fields = {k: v for k, v in obj.items() if k in t.model_fields}
    return t.model_validate(fields)


__all__ = [
    "named_data_schema",
    "product_schema",
    "upcast",
]
