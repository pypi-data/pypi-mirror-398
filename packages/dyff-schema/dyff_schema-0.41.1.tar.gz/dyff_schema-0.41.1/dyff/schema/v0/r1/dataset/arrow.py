# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
from __future__ import annotations

import functools
import inspect
import typing
import uuid
from typing import Any, Iterable, Literal, Optional

import pyarrow
import pyarrow.dataset
import pydantic
from pydantic.fields import FieldInfo

from ..base import DType
from . import binary

# ----------------------------------------------------------------------------
# Schema utilities


def arrow_schema(
    model_type: typing.Type[pydantic.BaseModel],
    *,
    metadata: Optional[dict[str, str]] = None,
) -> pyarrow.Schema:
    """Create an Arrow schema from a Pydantic model.

    We support a very basic subset of pydantic model features currently. The intention
    is to expand this.
    """
    arrow_fields = [
        arrow_field(name, field) for name, field in model_type.model_fields.items()
    ]
    return pyarrow.schema(arrow_fields, metadata=metadata)


def make_item_schema(schema: pyarrow.Schema) -> pyarrow.Schema:
    """Given an Arrow schema, create a new one that has the extra ``Item`` fields
    added."""
    return schema.insert(0, pyarrow.field("_index_", pyarrow.int64()))


def make_response_item_schema(schema: pyarrow.Schema) -> pyarrow.Schema:
    """Given an Arrow schema, create a new one that has the extra ``ResponseItem``
    fields added."""
    return schema.insert(0, pyarrow.field("_response_index_", pyarrow.int64()))


def make_response_schema(schema: pyarrow.Schema) -> pyarrow.Schema:
    """Given an Arrow schema, create a new one that has the extra ``ResponseItem``
    fields added."""
    response_item_schema = make_response_item_schema(schema)
    fields = [
        pyarrow.field(n, t)
        for n, t in zip(response_item_schema.names, response_item_schema.types)
    ]
    item_type = pyarrow.struct(fields)
    responses_type = pyarrow.list_(item_type)
    return pyarrow.schema(
        [
            pyarrow.field("_replication_", pyarrow.string()),
            pyarrow.field("_index_", pyarrow.int64()),
            pyarrow.field("responses", responses_type),
        ]
    )


def encode_schema(schema: pyarrow.Schema) -> str:
    """Encode an Arrow schema as a string."""
    # pyarrow.Buffer doesn't satisfy ReadableBuffer but it still works
    return binary.encode(schema.serialize())  # type: ignore[arg-type]


def decode_schema(schema: str) -> pyarrow.Schema:
    """Decode the string representation of an Arrow schema."""
    return pyarrow.ipc.read_schema(pyarrow.py_buffer(binary.decode(schema)))


def subset_schema(schema: pyarrow.Schema, field_names: list[str]) -> pyarrow.Schema:
    fields = []
    for field_name in field_names:
        field_index = schema.get_field_index(field_name)
        if field_index != -1:
            fields.append(schema.field(field_index))
        else:
            raise ValueError(f"unknown field name: '{field_name}'")
    return pyarrow.schema(fields)


def arrow_type(annotation: type) -> pyarrow.DataType:
    """Determine a suitable arrow type for a pydantic model field.

    Supports primitive types as well as pydantic sub-models, lists, and optional types.
    Numeric types must have appropriate bounds specified, as Arrow cannot represent the
    unbounded integer types used by Python 3.
    """
    if origin := typing.get_origin(annotation):
        if origin == list:
            annotation_args = typing.get_args(annotation)
            if len(annotation_args) != 1:
                raise ValueError(f"annotation {annotation}: expected 1 type arg")
            item_type = annotation_args[0]
            return pyarrow.list_(arrow_type(item_type))
        elif origin == typing.Union:
            annotation_args = typing.get_args(annotation)
            if len(annotation_args) != 2:
                raise ValueError(
                    f"annotation {annotation}: only Optional[T] supported, not general Union"
                )
            if annotation_args[0] == type(None):
                inner_type = annotation_args[1]
            elif annotation_args[1] == type(None):
                inner_type = annotation_args[0]
            else:
                raise ValueError(
                    f"annotation {annotation}: only Optional[T] supported, not general Union"
                )
            return arrow_type(inner_type)  # All Arrow types are nullable

        raise NotImplementedError(f"Python type {annotation}")

    if issubclass(annotation, pydantic.BaseModel):
        subfields = []
        for _name, subfield in annotation.model_fields.items():
            subfields.append(arrow_field(_name, subfield))
        return pyarrow.struct(subfields)

    # Handle numpy-like types
    if hasattr(annotation, "dtype"):
        return pyarrow.from_numpy_dtype(annotation.dtype)

    # Handle Annotated list types (e.g., Annotated[list[str], Field(max_length=10)])
    # This covers lists created by our list_() function in base.py which returns
    # Annotated types with Field metadata for length constraints.
    #
    # We need custom logic here because:
    # 1. Standard typing.List doesn't carry Pydantic Field constraints
    # 2. Our list_() function wraps list[T] in Annotated[list[T], Field(...)]
    #    to embed validation metadata (min/max length) at the type level
    # 3. PyArrow needs to know these constraints upfront to create proper schemas
    # 4. The nested generic structure requires careful extraction:
    #    Annotated[list[str], Field(max_length=10)] needs to become
    #    pyarrow.list_(pyarrow.string(), 10)
    if (
        typing.get_origin(annotation) is typing.Annotated
        and typing.get_args(annotation)[0] is list
    ):
        metadata = typing.get_args(annotation)[1:]
        item_type = typing.get_args(typing.get_args(annotation)[0])[0]
        max_length = -1
        for meta in metadata:
            if isinstance(meta, FieldInfo):
                max_length = getattr(meta, "max_length", -1)
        return pyarrow.list_(arrow_type(item_type), max_length)

    if issubclass(annotation, DType):
        # The dtype is in the metaclass
        return pyarrow.from_numpy_dtype(type(annotation).dtype)  # type: ignore[attr-defined]

    if annotation == bool:
        return pyarrow.bool_()
    if annotation == bytes:
        return pyarrow.binary()
    if annotation == float:
        return pyarrow.float64()
    if annotation == int:
        raise ValueError("unconstrained integers cannot be represented in Arrow")
    if annotation == uuid.UUID:
        return pyarrow.binary(16)

    if annotation == str:
        return pyarrow.string()

    raise NotImplementedError(f"Python type {annotation}")


def arrow_field(field_name: str, field_info: pydantic.fields.FieldInfo):
    """Create a named ``pyarrow.Field`` from a pydantic model ``ModelField``.

    If present, the ``.alias`` property of the ``ModelField`` takes precedence
    over its ``.name`` field. The type is determined by the ``arrow_type()``
    function. The ``.description`` property, if present, becomes the docstring
    for the arrow field.
    """
    name = field_info.alias if field_info.alias else field_name
    docstring = field_info.description
    return field_with_docstring(
        name, arrow_type(field_info.annotation or str), docstring=docstring
    )


def field_with_docstring(
    name: str | bytes,
    type: pyarrow.DataType,  # pylint: disable=redefined-builtin
    nullable: bool = True,
    metadata: dict | None = None,
    *,
    docstring: str | None = None,
) -> pyarrow.Field:
    """Wrapper for ``pyarrow.field()`` that adds a docstring in the ``__doc__`` property
    of ``metadata``."""
    if metadata:
        metadata_with_docstring = metadata.copy()
        if docstring:
            metadata_with_docstring["__doc__"] = docstring
    else:
        if docstring:
            metadata_with_docstring = {"__doc__": docstring}
        else:
            metadata_with_docstring = None
    return pyarrow.field(name, type, nullable, metadata_with_docstring)


def schema_function(schema: pyarrow.Schema):
    """Annotation for functions that return ``pyarrow.Schema``. The annotated function
    will return the supplied schema and will have a docstring describing the schema.

    Intended to be applied to a function with no body, e.g.:

    .. code-block:: python

      @schema_function(
        pyarrow.schema([
          field_with_docstring("field_name", pyarrow.string(), docstring="Very important!")
        ])
      )
      def schema() -> pyarrow.Schema:
        \"\"\"Additional docstring. Don't define a function body\"\"\"
    """

    def patch(f):
        if f.__doc__:
            docs = inspect.cleandoc(f.__doc__)
        else:
            docs = "pyarrow.Schema"

        @functools.wraps(f)
        def get(_selfish) -> pyarrow.Schema:
            return schema

        get.__doc__ = f"{docs}\n\n{schema_docstring(schema)}"
        return get

    return patch


def schema_docstring(schema: pyarrow.Schema) -> str:
    """Create a docstring for a ``pyarrow.Schema``."""
    fields = [schema.field(i) for i in range(len(schema.names))]
    lines = _construct_field_docs(fields)
    return "\n".join(lines)


def _construct_field_docs(
    fields: list[pyarrow.Field], *, _lines: list[str] | None = None, _depth=0
) -> list[str]:
    if _lines is None:
        _lines = []
    indent = "  " * _depth
    for field in fields:
        metadata = field.metadata or {}
        # metadata keys/values get coerced to bytes by pyarrow
        doc = metadata.get(b"__doc__", b"No description available").decode()
        _lines.append(f"{indent}{field.name} : {field.type}")
        _lines.append(f"{indent}  {doc}")

        if not pyarrow.types.is_nested(field.type):
            continue

        if pyarrow.types.is_struct(field.type):
            children = [field.type.field(i) for i in range(field.type.num_fields)]
        elif pyarrow.types.is_list(field.type):
            assert isinstance(field.type, pyarrow.ListType)
            children = [field.type.value_field]
        else:
            raise ValueError(f"Unsupported nested type {field.type}")

        _lines.append("")
        _construct_field_docs(children, _lines=_lines, _depth=(_depth + 1))
    return _lines


# ----------------------------------------------------------------------------
# Dataset utilities


def open_dataset(source: str | list[str]) -> pyarrow.dataset.Dataset:
    """Opens a ``pyarrow.dataset.Dataset.

    Args:
      source: Location of the dataset; either a directory or a list of files.
    """
    return pyarrow.dataset.dataset(
        source, partitioning="hive", format="parquet", ignore_prefixes=["."]
    )


def write_dataset(
    data_generator,
    *,
    output_path: str,
    feature_schema: pyarrow.Schema,
    partition_schema: Optional[pyarrow.Schema] = None,
    existing_data_behavior: Literal[
        "error", "overwrite_or_ignore", "delete_matching"
    ] = "overwrite_or_ignore",
    **kwargs,
):
    """Creates a ``pyarrow.dataset.Dataset`` from a data generator.

    Args:
      data_generator: A generator that yields ``pyarrow.RecordBatch`` instances.
      output_path: Location to store the ``pyarrow`` dataset. It could be a
        local directory or a Google Cloud Storage object URL (``gs://``).
      feature_schema: The ``pyarrow.Schema`` for the dataset.
      partition_schema: If not ``None``, the ``pyarrow.Schema`` describing the
        features that should be represented as partitions.
      existing_data_behavior: Same as ``pyarrow.dataset.write_dataset``, but
        defaults to ``"overwrite_or_ignore"``, which is typically what we want.
    """
    partitioning = (
        pyarrow.dataset.partitioning(partition_schema, flavor="hive")
        if partition_schema is not None
        else None
    )
    pyarrow.dataset.write_dataset(
        data_generator,
        output_path,
        format="parquet",
        schema=feature_schema,
        # Type annotation doesn't include PartitioningFactory even though
        # you're clearly meant to pass the output of partitioning() here
        partitioning=partitioning,  # type: ignore[arg-type]
        existing_data_behavior=existing_data_behavior,
        **kwargs,
    )


def batches(
    instances: Iterable[dict[str, Any]],
    *,
    batch_size: int,
    schema: Optional[pyarrow.Schema] = None,
) -> Iterable[pyarrow.RecordBatch]:
    """Group a stream of individual items into a stream of batches.

    :param instance: Stream of items in "pylist" format.
    :param batch_size: The maximum size of the batches. The final batch may
        be smaller than this if the number of instances is not divisible by
        the batch size.
    :param schema: The arrow schema for the batches. You should strongly
        consider specifying the schema explicitly. Arrow will try to infer
        one if you don't, and it often gets it wrong.
    :returns: A stream of ``pyarrow.RecordBatch`` instances.
    """
    batch = []
    for instance in instances:
        batch.append(instance)
        if len(batch) == batch_size:
            yield pyarrow.RecordBatch.from_pylist(batch, schema=schema)  # type: ignore[attr-defined]
            batch = []
    if batch:  # Final (incomplete) batch
        yield pyarrow.RecordBatch.from_pylist(batch, schema=schema)  # type: ignore[attr-defined]


__all__ = [
    "arrow_field",
    "arrow_schema",
    "arrow_type",
    "batches",
    "decode_schema",
    "encode_schema",
    "field_with_docstring",
    "make_item_schema",
    "make_response_item_schema",
    "make_response_schema",
    "open_dataset",
    "schema_docstring",
    "schema_function",
    "subset_schema",
    "write_dataset",
]
