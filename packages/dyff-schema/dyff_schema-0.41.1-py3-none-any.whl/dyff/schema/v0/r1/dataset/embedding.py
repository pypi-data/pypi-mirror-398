# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from typing import Type, Union

import pydantic
from typing_extensions import Annotated

from ..base import DyffSchemaBaseModel, float32, float64, list_


def embedding(
    element_type: Type[
        Union[
            Annotated[float, float32()],
            Annotated[float, float64()],
        ]
    ],
    size: int,
) -> Type[DyffSchemaBaseModel]:
    """Returns a schema type representing a list of fixed-length embedding vectors."""

    class _Embedding(DyffSchemaBaseModel):
        embedding: list_(element_type, list_size=size) = pydantic.Field(  # type: ignore[valid-type]
            description="An embedding vector"
        )

    return _Embedding


__all__ = [
    "embedding",
]
