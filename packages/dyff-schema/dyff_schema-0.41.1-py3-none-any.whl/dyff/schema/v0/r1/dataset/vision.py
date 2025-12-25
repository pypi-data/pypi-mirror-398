# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import pydantic

from ..base import DyffSchemaBaseModel


class Image(DyffSchemaBaseModel):
    """A binary-formatted image.

    ..deprecated:: Use binary.Media with an 'image/...' media type.
    """

    bytes_: bytes = pydantic.Field(alias="bytes", description="The image data")
    format: str = pydantic.Field(description="The data MIME type")
