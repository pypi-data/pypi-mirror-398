# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import pydantic

from ..base import DyffSchemaBaseModel


class Label(DyffSchemaBaseModel):
    """A single discrete label for an item."""

    label: str = pydantic.Field(description="The discrete label of the item")
