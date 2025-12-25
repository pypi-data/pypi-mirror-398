# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import base64
import hashlib
import typing

import pydantic

from ..base import DyffSchemaBaseModel

if typing.TYPE_CHECKING:
    from _typeshed import ReadableBuffer


def encode(data: "ReadableBuffer") -> str:
    return base64.b64encode(data).decode("utf-8")


def decode(data: str) -> bytes:
    return base64.b64decode(data)


def file_digest(algorithm: str, path: str) -> bytes:
    h = hashlib.new(algorithm)
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(path, "rb", buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.digest()


class Media(DyffSchemaBaseModel):
    """Binary-encoded data with accompanying media type."""

    data: bytes = pydantic.Field(description="The binary data")
    mediaType: str = pydantic.Field(
        description="The IETF Media Type (MIME type) of the data"
    )
