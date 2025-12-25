# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

from typing_extensions import TypeAlias

from .v0.r1.version import *
from .v0.r1.version import __all__ as __version_all__

SomeSchemaVersion: TypeAlias = Literal["0.1"]


V0_1: str = "0.1"


__all__ = __version_all__ + ["SomeSchemaVersion", "V0_1"]
