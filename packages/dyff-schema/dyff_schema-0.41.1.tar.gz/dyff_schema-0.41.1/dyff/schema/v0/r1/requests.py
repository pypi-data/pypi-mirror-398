# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0
"""The request schemas describe the information that you need to provide when creating
new instances of the core types.

For example, requests do not have
``.id`` fields because these are assigned by the platform when the resource
is created. Similarly, if a resource depends on an instance of another
resource, the request will refer to the dependency by its ID, while the core
resource will include the full dependency object as a sub-resource. The
``create`` endpoints take a request as input and return a full core resource
in response.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal, Optional, Union

import pydantic

from ... import upcast
from . import commands
from .base import DyffBaseModel, JsonMergePatchSemantics
from .platform import (
    AnalysisRequestBase,
    AnalysisScope,
    ChallengeContent,
    ChallengeTaskBase,
    ConcernBase,
    DatasetBase,
    DataView,
    DocumentationBase,
    Evaluation,
    EvaluationInferenceSessionRequest,
    EvaluationRequestBase,
    FamilyBase,
    FamilyMemberBase,
    InferenceServiceBase,
    InferenceSessionBase,
    MethodBase,
    ModelSpec,
    ModuleBase,
    PipelineBase,
    PipelineRunBase,
    ReportBase,
    SubmissionBase,
    TagNameType,
    TeamBase,
    summary_maxlen,
    title_maxlen,
)
from .version import SchemaVersion

# mypy gets confused because 'dict' is the name of a method in DyffBaseModel
_ModelAsDict = dict[str, Any]


class DyffRequestDefaultValidators(DyffBaseModel):
    """This must be the base class for *all* request models in the Dyff schema.

    Adds a root validator to ensure that all user-provided datetime fields have a
    timezone set. Timezones will be converted to UTC once the data enters the platform,
    but we allow requests to have non-UTC timezones for user convenience.
    """

    @pydantic.model_validator(mode="after")
    def _require_datetime_timezone_aware(self):
        for k, v in self.__dict__.items():
            if isinstance(v, datetime):
                if v.tzinfo is None:
                    raise ValueError(
                        f"{self.__class__.__qualname__}.{k}: timezone not set"
                    )
        return self


class DyffRequestBase(SchemaVersion, DyffRequestDefaultValidators):
    # TODO: (DYFF-223) I think that exclude_unset=True should be the default
    # for all schema objects, but I'm unsure of the consequences of making
    # this change and we'll defer it until v1.
    def model_dump(  # type: ignore [override]
        self, *, by_alias: bool = True, exclude_unset=True, **kwargs
    ) -> _ModelAsDict:
        return super().model_dump(
            by_alias=by_alias, exclude_unset=exclude_unset, **kwargs
        )

    def model_dump_json(  # type: ignore [override]
        self, *, by_alias: bool = True, exclude_unset=True, **kwargs
    ) -> str:
        return super().model_dump_json(
            by_alias=by_alias, exclude_unset=exclude_unset, **kwargs
        )

    def dict(
        self, *, by_alias: bool = True, exclude_unset=True, **kwargs
    ) -> _ModelAsDict:
        return super().model_dump(
            by_alias=by_alias, exclude_unset=exclude_unset, **kwargs
        )

    def json(self, *, by_alias: bool = True, exclude_unset=True, **kwargs) -> str:
        return super().model_dump_json(
            by_alias=by_alias, exclude_unset=exclude_unset, **kwargs
        )


# ----------------------------------------------------------------------------


class DyffEntityCreateRequest(DyffRequestBase):
    account: str = pydantic.Field(description="Account that owns the entity")


class AnalysisCreateRequest(DyffEntityCreateRequest, AnalysisRequestBase):
    """An Analysis transforms Datasets, Evaluations, and Measurements into new
    Measurements or SafetyCases."""

    @pydantic.field_validator("scope", check_fields=False)
    def _validate_scope(cls, scope: AnalysisScope) -> AnalysisScope:
        # TODO: This has to be a validator function because we can't apply the
        # regex contraint to AnalysisScope, since there are already entities
        # with invalid IDs in the data store. Fix in Schema v1.
        uuid4 = r"^[0-9a-f]{8}[0-9a-f]{4}[4][0-9a-f]{3}[89ab][0-9a-f]{3}[0-9a-f]{12}$"
        id_pattern = re.compile(uuid4)
        if scope.dataset is not None and not re.match(id_pattern, scope.dataset):
            raise ValueError("scope.dataset must be an entity ID")
        if scope.evaluation is not None and not re.match(id_pattern, scope.evaluation):
            raise ValueError("scope.evaluation must be an entity ID")
        if scope.inferenceService is not None and not re.match(
            id_pattern, scope.inferenceService
        ):
            raise ValueError("scope.inferenceService must be an entity ID")
        if scope.model is not None and not re.match(id_pattern, scope.model):
            raise ValueError("scope.model must be an entity ID")
        return scope


class ArtifactCreateRequest(DyffEntityCreateRequest):
    pass


class ChallengeCreateRequest(DyffEntityCreateRequest):
    content: ChallengeContent = pydantic.Field(
        default_factory=ChallengeContent,
        description="Content of the challenge view in the Dyff App.",
    )


class SubmissionCreateRequest(DyffEntityCreateRequest, SubmissionBase):
    pass


class ChallengeTaskCreateRequest(DyffEntityCreateRequest, ChallengeTaskBase):
    pass


class ChallengeTeamCreateRequest(DyffEntityCreateRequest, TeamBase):
    pass


class ConcernCreateRequest(DyffEntityCreateRequest, ConcernBase):
    @pydantic.field_validator("documentation", check_fields=False)
    def _validate_documentation(
        cls, documentation: DocumentationBase
    ) -> DocumentationBase:
        # TODO: This has to be a validator function because we can't apply the
        # contraint to DocumentationBase, since there are already entities
        # that violate the constraints in the data store. Fix in Schema v1.
        if (
            documentation.title is not None
            and len(documentation.title) > title_maxlen()
        ):
            raise ValueError(
                f".documentation.title must have length < {title_maxlen()}"
            )
        if (
            documentation.summary is not None
            and len(documentation.summary) > summary_maxlen()
        ):
            raise ValueError(
                f".documentation.summary must have length < {summary_maxlen()}"
            )
        return documentation


class DatasetCreateRequest(DyffEntityCreateRequest, DatasetBase):
    pass


class InferenceServiceCreateRequest(DyffEntityCreateRequest, InferenceServiceBase):
    model: Optional[str] = pydantic.Field(
        default=None, description="ID of Model backing the service, if applicable"
    )

    @pydantic.model_validator(mode="after")
    def check_runner_and_image_specified(self):
        if self.runner is None:
            raise ValueError("must specify .runner in new inference services")
        image = self.runner.image is not None
        imageRef = self.runner.imageRef is not None
        if sum([image, imageRef]) != 1:
            raise ValueError("must specify exactly one of .runner.{image, imageRef}")
        return self


class InferenceSessionCreateRequest(DyffEntityCreateRequest, InferenceSessionBase):
    inferenceService: str = pydantic.Field(description="InferenceService ID")


class InferenceSessionTokenCreateRequest(DyffRequestBase):
    expires: Optional[datetime] = pydantic.Field(
        default=None,
        description="Expiration time of the token. Must be <= expiration time"
        " of session. Default: expiration time of session.",
    )


class EvaluationCreateRequest(DyffEntityCreateRequest, EvaluationRequestBase):
    """A description of how to run an InferenceService on a Dataset to obtain a set of
    evaluation results."""

    @staticmethod
    def repeat_of(evaluation: Evaluation) -> EvaluationCreateRequest:
        """Return a request that will run an existing Evaluation again with the same
        configuration."""
        base = upcast(EvaluationRequestBase, evaluation)
        if evaluation.inferenceSessionReference:
            return EvaluationCreateRequest(
                account=evaluation.account,
                inferenceSessionReference=evaluation.inferenceSessionReference,
                **base.model_dump(),
            )
        else:
            return EvaluationCreateRequest(
                account=evaluation.account,
                inferenceSession=EvaluationInferenceSessionRequest(
                    inferenceService=evaluation.inferenceSession.inferenceService.id,
                    **upcast(
                        InferenceSessionBase, evaluation.inferenceSession
                    ).model_dump(),
                ),
                **base.model_dump(),
            )


class FamilyCreateRequest(DyffEntityCreateRequest, FamilyBase):
    pass


class MethodCreateRequest(DyffEntityCreateRequest, MethodBase):
    pass


class ModelCreateRequest(DyffEntityCreateRequest, ModelSpec):
    pass


class ModuleCreateRequest(DyffEntityCreateRequest, ModuleBase):
    pass


class PipelineCreateRequest(DyffEntityCreateRequest, PipelineBase):
    pass


class PipelineRunRequest(DyffEntityCreateRequest, PipelineRunBase):
    pass


class ReportCreateRequest(DyffEntityCreateRequest, ReportBase):
    """A Report transforms raw model outputs into some useful statistics.

    .. deprecated:: 0.8.0

        Report functionality has been refactored into the
        Method/Measurement/Analysis apparatus. Creation of new Reports is
        disabled.
    """

    datasetView: Optional[Union[str, DataView]] = pydantic.Field(
        default=None,
        description="View of the input dataset required by the report (e.g., ground-truth labels).",
    )

    evaluationView: Optional[Union[str, DataView]] = pydantic.Field(
        default=None,
        description="View of the evaluation output data required by the report.",
    )


# ----------------------------------------------------------------------------


class ChallengeContentEditRequest(DyffRequestBase, commands.EditChallengeContentPatch):
    pass


class ChallengeTaskRulesEditRequest(DyffRequestBase, commands.ChallengeTaskRulesPatch):
    pass


class DocumentationEditRequest(
    DyffRequestBase, commands.EditEntityDocumentationAttributes
):
    pass


class FamilyMembersEditRequest(DyffRequestBase, JsonMergePatchSemantics):
    members: dict[TagNameType, Optional[FamilyMemberBase]] = pydantic.Field(
        description="Mapping of names to IDs of member resources.",
    )


class LabelsEditRequest(DyffRequestBase, commands.EditEntityLabelsAttributes):
    pass


class LabelUpdateRequest(LabelsEditRequest):
    """Deprecated alias for LabelsEditRequest.

    .. deprecated:: 0.26.0

        Use LabelsEditRequest
    """


class TeamEditRequest(DyffRequestBase, commands.EditTeamAttributes):
    pass


# ----------------------------------------------------------------------------


# Note: Query requests, as they currently exist, don't work with Versioned
# because fastapi will assign None to every field that the client doesn't
# specify. I think it's not that important, because all of the query parameters
# will always be optional. There could be a problem if the semantics of a
# name change, but let's just not do that!
class QueryRequest(DyffRequestDefaultValidators):
    query: Optional[str] = pydantic.Field(
        default=None,
        description="A JSON structure describing a query, encoded as a string."
        " Valid keys are the same as the valid query keys for the corresponding"
        " endpoint. Values can be scalars or lists. Lists are treated as"
        " disjunctive queries (i.e., 'value $in list').",
    )

    id: Optional[str] = pydantic.Field(default=None)

    order: Optional[Literal["ascending", "descending"]] = pydantic.Field(
        default=None,
        description="Sort the results in this order. Default: unsorted."
        " Ignored unless 'orderBy' is also set."
        " The order of operations is query -> order -> limit.",
    )

    orderBy: Optional[str] = pydantic.Field(
        default=None,
        description="Sort the results by the value of the specified field."
        " The 'order' field must be set also."
        " The order of operations is query -> order -> limit.",
    )

    limit: Optional[int] = pydantic.Field(
        default=None,
        ge=1,
        description="Return at most this many results."
        " The order of operations is query -> order -> limit.",
    )


class DyffEntityQueryRequest(QueryRequest):
    account: Optional[str] = pydantic.Field(default=None)
    status: Optional[str] = pydantic.Field(default=None)
    reason: Optional[str] = pydantic.Field(default=None)
    labels: Optional[str] = pydantic.Field(
        default=None, description="Labels dict represented as a JSON string."
    )


class DocumentationQueryRequest(QueryRequest):
    pass


class _AnalysisProductQueryRequest(DyffEntityQueryRequest):
    method: Optional[str] = pydantic.Field(default=None)
    methodName: Optional[str] = pydantic.Field(default=None)
    dataset: Optional[str] = pydantic.Field(default=None)
    evaluation: Optional[str] = pydantic.Field(default=None)
    inferenceService: Optional[str] = pydantic.Field(default=None)
    model: Optional[str] = pydantic.Field(default=None)
    inputs: Optional[str] = pydantic.Field(default=None)


class ArtifactQueryRequest(DyffEntityQueryRequest):
    name: Optional[str] = pydantic.Field(default=None)


class AuditQueryRequest(DyffEntityQueryRequest):
    name: Optional[str] = pydantic.Field(default=None)


class ChallengeQueryRequest(DyffEntityQueryRequest):
    pass


class DatasetQueryRequest(DyffEntityQueryRequest):
    name: Optional[str] = pydantic.Field(default=None)


class EvaluationQueryRequest(DyffEntityQueryRequest):
    dataset: Optional[str] = pydantic.Field(default=None)
    inferenceService: Optional[str] = pydantic.Field(default=None)
    inferenceServiceName: Optional[str] = pydantic.Field(default=None)
    model: Optional[str] = pydantic.Field(default=None)
    modelName: Optional[str] = pydantic.Field(default=None)


class FamilyQueryRequest(DyffEntityQueryRequest):
    pass


class InferenceServiceQueryRequest(DyffEntityQueryRequest):
    name: Optional[str] = pydantic.Field(default=None)
    model: Optional[str] = pydantic.Field(default=None)
    modelName: Optional[str] = pydantic.Field(default=None)


class InferenceSessionQueryRequest(DyffEntityQueryRequest):
    name: Optional[str] = pydantic.Field(default=None)
    inferenceService: Optional[str] = pydantic.Field(default=None)
    inferenceServiceName: Optional[str] = pydantic.Field(default=None)
    model: Optional[str] = pydantic.Field(default=None)
    modelName: Optional[str] = pydantic.Field(default=None)


class MeasurementQueryRequest(_AnalysisProductQueryRequest):
    pass


class MethodQueryRequest(DyffEntityQueryRequest):
    name: Optional[str] = pydantic.Field(default=None)
    outputKind: Optional[str] = pydantic.Field(default=None)


class ModelQueryRequest(DyffEntityQueryRequest):
    name: Optional[str] = pydantic.Field(default=None)


class ModuleQueryRequest(DyffEntityQueryRequest):
    name: Optional[str] = pydantic.Field(default=None)


class ReportQueryRequest(DyffEntityQueryRequest):
    report: Optional[str] = pydantic.Field(default=None)
    dataset: Optional[str] = pydantic.Field(default=None)
    evaluation: Optional[str] = pydantic.Field(default=None)
    inferenceService: Optional[str] = pydantic.Field(default=None)
    model: Optional[str] = pydantic.Field(default=None)


class SafetyCaseQueryRequest(_AnalysisProductQueryRequest):
    pass


class ScoreQueryRequest(DyffRequestDefaultValidators):
    query: Optional[str] = pydantic.Field(
        default=None,
        description="A JSON structure describing a query, encoded as a string."
        " Valid keys are the same as the valid query keys for the corresponding"
        " endpoint. Values can be scalars or lists. Lists are treated as"
        " disjunctive queries (i.e., 'value $in list').",
    )

    id: Optional[str] = pydantic.Field(default=None)
    name: Optional[str] = pydantic.Field(default=None)
    analysis: Optional[str] = pydantic.Field(default=None)
    method: Optional[str] = pydantic.Field(default=None)
    methodName: Optional[str] = pydantic.Field(default=None)
    dataset: Optional[str] = pydantic.Field(default=None)
    evaluation: Optional[str] = pydantic.Field(default=None)
    inferenceService: Optional[str] = pydantic.Field(default=None)
    model: Optional[str] = pydantic.Field(default=None)


class SubmissionQueryRequest(DyffEntityQueryRequest):
    challenge: Optional[str] = pydantic.Field(default=None)
    task: Optional[str] = pydantic.Field(default=None)
    team: Optional[str] = pydantic.Field(default=None)
    pipelineRun: Optional[str] = pydantic.Field(default=None)


class TeamQueryRequest(DyffEntityQueryRequest):
    challenge: Optional[str] = pydantic.Field(default=None)


class UseCaseQueryRequest(DyffEntityQueryRequest):
    pass


__all__ = [
    "AnalysisCreateRequest",
    "ArtifactCreateRequest",
    "ArtifactQueryRequest",
    "AuditQueryRequest",
    "ChallengeContentEditRequest",
    "ChallengeCreateRequest",
    "ChallengeQueryRequest",
    "ChallengeTaskCreateRequest",
    "ChallengeTaskRulesEditRequest",
    "ChallengeTeamCreateRequest",
    "ConcernCreateRequest",
    "DyffEntityCreateRequest",
    "DyffEntityQueryRequest",
    "DyffRequestBase",
    "DyffRequestDefaultValidators",
    "DatasetCreateRequest",
    "DatasetQueryRequest",
    "DocumentationEditRequest",
    "DocumentationQueryRequest",
    "EvaluationCreateRequest",
    "EvaluationQueryRequest",
    "EvaluationInferenceSessionRequest",
    "FamilyCreateRequest",
    "FamilyMembersEditRequest",
    "FamilyQueryRequest",
    "InferenceServiceCreateRequest",
    "InferenceServiceQueryRequest",
    "InferenceSessionCreateRequest",
    "InferenceSessionQueryRequest",
    "InferenceSessionTokenCreateRequest",
    "LabelUpdateRequest",
    "LabelsEditRequest",
    "MeasurementQueryRequest",
    "MethodCreateRequest",
    "MethodQueryRequest",
    "ModelCreateRequest",
    "ModelQueryRequest",
    "ModuleCreateRequest",
    "ModuleQueryRequest",
    "PipelineCreateRequest",
    "PipelineRunRequest",
    "QueryRequest",
    "ReportCreateRequest",
    "ReportQueryRequest",
    "SafetyCaseQueryRequest",
    "ScoreQueryRequest",
    "SubmissionCreateRequest",
    "SubmissionQueryRequest",
    "TeamEditRequest",
    "TeamQueryRequest",
    "UseCaseQueryRequest",
]
