# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from typing import Type

import pydantic

from ..base import DyffSchemaBaseModel, int64, list_


# TODO: Make this configurable (?)
# Difficulty is that you have to use the same value when creating a signed
# URL and using the signed URL.
def max_artifact_size_bytes() -> int:
    return 1073741824


class Item(DyffSchemaBaseModel):
    """An individual indexed item within a dataset.

    This will often be a base class of items in an input dataset.
    """

    index: int64(ge=0) = pydantic.Field(  # type: ignore
        alias="_index_", description="The index of the item in the dataset"
    )


class ReplicatedItem(Item):
    """An indexed item that is part of a replication.

    This will often be a base class of outputs of ``Evaluation``s and
    ``Report``s.
    """

    replication: str = pydantic.Field(
        alias="_replication_",
        description="ID of the replication the item belongs to.",
    )


class ResponseItem(DyffSchemaBaseModel):
    """An individual indexed response to an indexed item within a dataset."""

    response_index: int64(ge=0) = pydantic.Field(  # type: ignore
        alias="_response_index_",
        description="The index of the response among responses to the corresponding _index_",
    )


def make_item_type(schema: Type[DyffSchemaBaseModel]) -> Type[DyffSchemaBaseModel]:
    """Return a pydantic model type that inherits from both ``Item`` and ``schema``."""
    return pydantic.create_model(f"{schema.__name__}Item", __base__=(schema, Item))


def make_response_item_type(
    schema: Type[DyffSchemaBaseModel],
) -> Type[DyffSchemaBaseModel]:
    """Return a pydantic model type that inherits from both ``ResponseItem`` and
    ``schema``."""
    return pydantic.create_model(
        f"{schema.__name__}ResponseItem", __base__=(schema, ResponseItem)
    )


def make_response_type(schema: Type[DyffSchemaBaseModel]) -> Type[DyffSchemaBaseModel]:
    """Return a pydantic model type that subclasses ``Item`` and has a field
    ``.responses`` of type ``list[schema]``."""

    response_item_t = make_response_item_type(schema)

    class Response(ReplicatedItem):
        responses: list_(response_item_t) = pydantic.Field(  # type: ignore
            description="Inference responses"
        )

    return Response


__all__ = [
    "Item",
    "ReplicatedItem",
    "ResponseItem",
    "make_item_type",
    "make_response_item_type",
    "make_response_type",
    "max_artifact_size_bytes",
]
