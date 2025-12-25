# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0
"""API response schemas for dyff platform endpoints.

These types represent the structured responses returned by dyff API endpoints. They are
shared between the API server and client libraries to ensure consistent data structures.
"""

from __future__ import annotations

from typing import Dict, List

import pydantic

from .base import DyffSchemaBaseModel
from .platform import EntityIdentifier


class WorkflowLogEntry(DyffSchemaBaseModel):
    """A single log entry from workflow infrastructure logs."""

    timestamp: str = pydantic.Field(description="ISO 8601 timestamp")
    message: str = pydantic.Field(description="Log message content")
    labels: Dict[str, str] = pydantic.Field(
        description="Kubernetes labels associated with the log entry"
    )


class WorkflowLogsResponse(DyffSchemaBaseModel):
    """Response from workflow logs endpoint."""

    workflow: EntityIdentifier = pydantic.Field(
        description="Entity that generated these workflow logs"
    )
    logs: List[WorkflowLogEntry] = pydantic.Field(
        description="Log entries from the workflow execution"
    )
    totalLines: int = pydantic.Field(description="Total number of log lines available")
