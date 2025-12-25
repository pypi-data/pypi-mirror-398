# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

import pydantic

SCHEMA_VERSION: str = "0.1"


class SchemaVersion(pydantic.BaseModel):
    schemaVersion: Literal["0.1"] = pydantic.Field(
        default=SCHEMA_VERSION,  # type: ignore [arg-type]
        description="The schema version.",
    )


__all__ = [
    "SCHEMA_VERSION",
    "SchemaVersion",
]
