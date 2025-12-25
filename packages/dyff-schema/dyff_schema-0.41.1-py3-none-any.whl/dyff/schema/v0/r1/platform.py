# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0
# fmt: off
"""Schema for the internal data representation of Dyff entities.

We use the following naming convention:

    * ``<Entity>``: A full-fledged entity that is tracked by the platform. It has
      an .id and the other dynamic system attributes like 'status'.
    * ``<Entity>Base``: The attributes of the Entity that are also attributes of
      the corresponding CreateRequest. Example: Number of replicas to use for
      an evaluation.
    * ``Foreign<Entity>``: Like <Entity>, but without dynamic system fields
      like 'status'. This type is used when we want to embed the full
      description of a resource inside of an outer resource that depends on it.
      We include the full dependency data structure so that downstream
      components don't need to be able to look it up by ID.
"""

# fmt: on
# mypy: disable-error-code="import-untyped"
from __future__ import annotations

import abc
import enum
import urllib.parse
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Literal,
    NamedTuple,
    Optional,
    Type,
    TypeVar,
    Union,
)

import i18naddress
import pyarrow
import pydantic
from pydantic import StringConstraints
from typing_extensions import Annotated, TypeAlias

from ... import named_data_schema, product_schema
from ...version import SomeSchemaVersion
from . import oci
from .base import DyffSchemaBaseModel
from .dataset import arrow, make_item_type, make_response_type
from .version import SCHEMA_VERSION, SchemaVersion

SYSTEM_ATTRIBUTES = frozenset(["creationTime", "status", "reason"])


def _k8s_quantity_regex():
    # This is copy-pasted from the regex that operator-sdk generates for resource.Quantity types
    return r"^(\+|-)?(([0-9]+(\.[0-9]*)?)|(\.[0-9]+))(([KMGTPE]i)|[numkMGTPE]|([eE](\+|-)?(([0-9]+(\.[0-9]*)?)|(\.[0-9]+))))?$"


def _k8s_label_regex():
    """A k8s label is like a DNS label but also allows ``.`` an ``_`` as separator
    characters."""
    return r"[a-z0-9A-Z]([-_.a-z0-9A-Z]{0,61}[a-z0-9A-Z])?"


def _k8s_label_maxlen():
    """Max length of a k8s label, same as for a DNS label."""
    return 63


def _dns_label_regex():
    """Alphanumeric characters separated by ``-``, maximum of 63 characters."""
    return r"[a-zA-Z0-9]([-a-zA-Z0-9]{0,61}[a-zA-Z0-9])?"


def _dns_label_maxlen():
    """Max length of a DNS label."""
    return 63


def _dns_domain_regex():
    """One or more DNS labels separated by dots (``.``).

    Note that its maximum length is 253 characters, but we can't enforce this in the
    regex.
    """
    return rf"{_dns_label_regex()}(\.{_dns_label_regex()})*"


def _k8s_domain_maxlen():
    """Max length of a k8s domain.

    The DNS domain standard specifies 255 characters, but this includes the trailing dot
    and null terminator. We never include a trailing dot in k8s-style domains.
    """
    return 253


def _k8s_label_key_regex():
    """The format of keys for labels and annotations. Optional subdomain prefix followed
    by a k8s label.

    See: https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/

    Valid label keys have two segments: an optional prefix and name, separated
    by a slash (``/``). The name segment is required and must have 63 characters
    or fewer, consisting of alphanumeric characters separated by ``-``, ``.``,
    or ``_`` characters. The prefix is optional. If specified, it must be a
    DNS subdomain followed by a ``/`` character.

    Examples:

        * my-multi_segment.key
        * dyff.io/reserved-key
    """
    return rf"^({_dns_domain_regex()}/)?{_dns_label_regex()}$"


def _k8s_label_key_maxlen():
    """Max length of a label key.

    The prefix segment, if present, has a max length of 253 characters. The
    name segment has a max length of 63 characters.

    See: https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/
    """
    # subdomain + '/' + label
    # Note that the domain regex can't enforce its max length because it can
    # have an arbitrary number of parts (part1.part2...), but the label regex
    # *does* enforce a max length, so checking the overall length is sufficient
    # to limit the domain part to 253 characters.
    return _k8s_domain_maxlen() + 1 + _k8s_label_maxlen()


def _k8s_label_value_regex():
    """The format of values for labels.

    Label values must satisfy the following:

        * must have 63 characters or fewer (can be empty)
        * unless empty, must begin and end with an alphanumeric character (``[a-z0-9A-Z]``)
        * could contain dashes (``-``), underscores (``_``), dots (``.``), and alphanumerics between

    See: https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/
    """
    return rf"^({_k8s_label_regex()})?$"


def _k8s_label_value_maxlen():
    """Max length of a label value.

    Label values must have 63 characters or fewer (can be empty).

    See: https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/
    """
    return _k8s_label_maxlen()


def _oci_image_tag_regex():
    """Regex matching valid image tags according to the OCI spec.

    See: https://github.com/opencontainers/distribution-spec/blob/main/spec.md#pull
    """
    return r"^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$"


def _oci_image_tag_maxlen():
    """Max length of valid image tags according to the OCI spec.

    See: https://github.com/opencontainers/distribution-spec/blob/main/spec.md#pull
    """
    return 127


def identifier_regex():
    """Python identifiers start with a letter or an underscore, and consist of letters,
    numbers, and underscores."""
    return r"^[a-zA-Z_][a-zA-Z0-9_]*$"


def identifier_maxlen():
    """There isn't really a max length for Python identifiers, but this seems like a
    reasonable limit for our use."""
    return 127


def title_maxlen() -> int:
    return 140


def summary_maxlen() -> int:
    return 280


def body_maxlen() -> int:
    return 1_000_000


def entity_id_regex() -> str:
    """An entity ID is a 32-character HEX string.

    TODO: This doesn't check whether the hex string is a valid UUID.
    """
    return r"^[a-f0-9]{32}$"


class Entities(str, enum.Enum):
    """The kinds of entities in the dyff system."""

    Account = "Account"
    Analysis = "Analysis"
    # FIXME: (schema v1) Rename to Artifact
    Artifact = "OCIArtifact"
    Audit = "Audit"
    AuditProcedure = "AuditProcedure"
    Challenge = "Challenge"
    Concern = "Concern"
    Curve = "Curve"
    DataSource = "DataSource"
    Dataset = "Dataset"
    Documentation = "Documentation"
    Evaluation = "Evaluation"
    Family = "Family"
    Hazard = "Hazard"
    History = "History"
    InferenceService = "InferenceService"
    InferenceSession = "InferenceSession"
    Measurement = "Measurement"
    Method = "Method"
    Model = "Model"
    Module = "Module"
    Pipeline = "Pipeline"
    PipelineRun = "PipelineRun"
    Report = "Report"
    Revision = "Revision"
    SafetyCase = "SafetyCase"
    Score = "Score"
    Submission = "Submission"
    Team = "Team"
    UseCase = "UseCase"

    @staticmethod
    def for_type(t: type["DyffEntityT"]) -> "Entities":
        try:
            return Entities(t.__name__)
        except ValueError:
            raise ValueError(f"not a DyffEntity type: {t}")


class Resources(str, enum.Enum):
    """The resource names corresponding to entities that have API endpoints."""

    Analysis = "analyses"
    Artifact = "artifacts"
    Audit = "audits"
    AuditProcedure = "auditprocedures"
    Challenge = "challenges"
    Concern = "concerns"
    Curve = "curves"
    Dataset = "datasets"
    DataSource = "datasources"
    Descriptor = "descriptors"
    Documentation = "documentation"
    Evaluation = "evaluations"
    Family = "families"
    Hazard = "hazards"
    History = "histories"
    InferenceService = "inferenceservices"
    InferenceSession = "inferencesessions"
    Measurement = "measurements"
    Method = "methods"
    Model = "models"
    Module = "modules"
    Pipeline = "pipelines"
    PipelineRun = "pipelineruns"
    Report = "reports"
    Revision = "revisions"
    SafetyCase = "safetycases"
    Score = "scores"
    Submission = "submissions"
    Team = "teams"
    UseCase = "usecases"

    Task = "tasks"
    """
    .. deprecated:: 0.5.0

        The Task resource no longer exists, but removing this enum entry
        breaks existing API keys.
    """

    ChoresValidateSchema = "chores/validate-schema"
    """Administrative task: Schema validation operations."""

    ALL = "*"

    @staticmethod
    def for_kind(kind: Entities) -> "Resources":
        try:
            # FIXME: (schema v1) Special case for legacy OCIArtifact name
            if kind == Entities.Artifact:
                return Resources.Artifact
            return Resources[kind.value]
        except KeyError:
            raise ValueError(f"No Resources for Entity kind: {kind}")


EntityKindLiteral = Literal[
    "Analysis",
    "Audit",
    "AuditProcedure",
    "Challenge",
    "Curve",
    "DataSource",
    "Dataset",
    "Evaluation",
    "Family",
    "Hazard",
    "History",
    "InferenceService",
    "InferenceSession",
    "Measurement",
    "Method",
    "Model",
    "Module",
    # FIXME: (schema v1) Rename to Artifact
    "OCIArtifact",
    "Pipeline",
    "PipelineRun",
    "Report",
    "Revision",
    "SafetyCase",
    "Submission",
    "Team",
    "UseCase",
]


EntityID: TypeAlias = Annotated[str, StringConstraints(pattern=entity_id_regex())]  # type: ignore


class DyffModelWithID(DyffSchemaBaseModel):
    id: str = pydantic.Field(description="Unique identifier of the entity")
    account: str = pydantic.Field(description="Account that owns the entity")


class EntityIdentifier(DyffSchemaBaseModel):
    """Identifies a single entity."""

    @staticmethod
    def of(entity: "DyffEntityType") -> "EntityIdentifier":
        """Create an identifier that identifies the given entity."""
        return EntityIdentifier(kind=entity.kind, id=entity.id)

    id: str = pydantic.Field(description="The .id of the entity.")
    kind: EntityKindLiteral = pydantic.Field(
        description="The .kind of the entity.",
    )

    def resource_path(self) -> str:
        return f"{Resources.for_kind(Entities(self.kind)).value}/{self.id}"


def LabelKey() -> type[str]:
    return Annotated[
        str,
        StringConstraints(
            pattern=_k8s_label_key_regex(), max_length=_k8s_label_key_maxlen()
        ),
    ]  # type: ignore [return-value]


def LabelValue() -> type[str]:
    return Annotated[
        str,
        StringConstraints(
            pattern=_k8s_label_value_regex(), max_length=_k8s_label_value_maxlen()
        ),
    ]  # type: ignore [return-value]


def TagName() -> type[str]:
    return Annotated[
        str,
        StringConstraints(
            pattern=_oci_image_tag_regex(), max_length=_oci_image_tag_maxlen()
        ),
    ]  # type: ignore [return-value]


LabelKeyType: TypeAlias = LabelKey()  # type: ignore

LabelValueType: TypeAlias = LabelValue()  # type: ignore

TagNameType: TypeAlias = TagName()  # type: ignore


class Label(DyffSchemaBaseModel):
    """A key-value label for a resource. Used to specify identifying attributes of
    resources that are meaningful to users but do not imply semantics in the dyff
    system.

    We follow the kubernetes label conventions closely. See:
    https://kubernetes.io/docs/concepts/overview/working-with-objects/labels
    """

    key: LabelKeyType = pydantic.Field(  # type: ignore
        description="The label key is a DNS label with an optional DNS domain"
        " prefix. For example: 'my-key', 'your.com/key_0'. Keys prefixed with"
        " 'dyff.io/', 'subdomain.dyff.io/', etc. are reserved.",
    )

    value: LabelValueType = pydantic.Field(  # type: ignore
        description="The label value consists of alphanumeric characters"
        " separated by '.', '-', or '_'.",
    )


class Labeled(DyffSchemaBaseModel):
    labels: dict[LabelKeyType, LabelValueType] = pydantic.Field(  # type: ignore
        default_factory=dict,
        description="A set of key-value labels for the resource. Used to"
        " specify identifying attributes of resources that are meaningful to"
        " users but do not imply semantics in the dyff system.\n\n"
        "The keys are DNS labels with an optional DNS domain prefix."
        " For example: 'my-key', 'your.com/key_0'. Keys prefixed with"
        " 'dyff.io/', 'subdomain.dyff.io/', etc. are reserved.\n\n"
        "The label values are alphanumeric characters separated by"
        " '.', '-', or '_'.\n\n"
        "We follow the kubernetes label conventions closely."
        " See: https://kubernetes.io/docs/concepts/overview/working-with-objects/labels",
        # Forbid entries that don't match the key patternProperties
        json_schema_extra={"additionalProperties": False},
    )


class Annotation(DyffSchemaBaseModel):
    key: str = pydantic.Field(
        pattern=_k8s_label_key_regex(),
        max_length=_k8s_label_key_maxlen(),
        description="The annotation key. A DNS label with an optional DNS domain prefix."
        " For example: 'my-key', 'your.com/key_0'. Names prefixed with"
        " 'dyff.io/', 'subdomain.dyff.io/', etc. are reserved.\n\n"
        "See https://kubernetes.io/docs/concepts/overview/working-with-objects/annotations"
        " for detailed naming rules.",
    )

    value: str = pydantic.Field(
        description="The annotation value. An arbitrary string."
    )


Quantity: TypeAlias = Annotated[str, StringConstraints(pattern=_k8s_quantity_regex())]  # type: ignore


class ServiceClass(str, enum.Enum):
    """Defines the "quality of service" characteristics of a resource allocation."""

    STANDARD = "standard"
    PREEMPTIBLE = "preemptible"


class ResourceAllocation(DyffSchemaBaseModel):
    quantities: dict[LabelKeyType, Quantity] = pydantic.Field(  # type: ignore
        default_factory=dict,
        description="Mapping of resource keys to quantities to be allocated.",
    )

    serviceClass: ServiceClass = pydantic.Field(description="The service class")


class Status(DyffSchemaBaseModel):
    status: str = pydantic.Field(
        description="Top-level resource status (assigned by system)"
    )

    reason: Optional[str] = pydantic.Field(
        default=None, description="Reason for current status (assigned by system)"
    )


class DocumentationBase(DyffSchemaBaseModel):
    title: Optional[str] = pydantic.Field(
        default=None,
        description='A short plain string suitable as a title or "headline".',
    )

    summary: Optional[str] = pydantic.Field(
        default=None,
        description="A brief summary, suitable for display in"
        " small UI elements. Interpreted as Markdown. Excessively long"
        " summaries may be truncated in the UI, especially on small displays.",
    )

    fullPage: Optional[str] = pydantic.Field(
        default=None,
        description="Long-form documentation. Interpreted as"
        " Markdown. There are no length constraints, but be reasonable.",
    )


class Documentation(SchemaVersion, DocumentationBase):
    entity: Optional[str] = pydantic.Field(
        default=None,
        description="The ID of the documented entity. This is Optional for"
        " backward compatibility but it will always be populated in API responses.",
    )


class Documented(DyffSchemaBaseModel):
    documentation: DocumentationBase = pydantic.Field(
        default_factory=DocumentationBase,
        description="Documentation of the resource. The content is used to"
        " populate various views in the web UI.",
    )


class Metadata(DyffSchemaBaseModel):
    pass


class Mutable(DyffSchemaBaseModel):
    etag: str
    lastModificationTime: datetime


class SecurityContext(DyffSchemaBaseModel):
    trusted: bool = pydantic.Field(
        default=True, description="Whether the workload is trusted."
    )


class MetricValue(DyffSchemaBaseModel):
    """A single labeled metric value."""

    labels: dict[str, str] = pydantic.Field(description="Metric labels")
    timestamp: datetime = pydantic.Field(
        description="When the metric value was captured"
    )
    value: float = pydantic.Field(description="The metric value")


class Metrics(DyffSchemaBaseModel):
    """Prometheus metrics captured at workflow completion.

    Stores final scalar values for each metric.
    """

    data: dict[str, list[MetricValue]] = pydantic.Field(
        default_factory=dict,
        description="Metrics data keyed by metric name",
    )


class DyffEntityMetadata(DyffSchemaBaseModel):
    metrics: Optional[Metrics] = pydantic.Field(
        default=None,
        description="Prometheus metrics captured when the workflow completes.",
    )

    revision: Optional[str] = pydantic.Field(
        default=None,
        description="Unique identifier of the current revision of the entity.",
    )

    documentation: DocumentationBase = pydantic.Field(
        default_factory=DocumentationBase,
        description="Documentation of the resource. The content is used to"
        " populate various views in the web UI.",
    )

    preconditions: list[EntityIdentifier] = pydantic.Field(
        default_factory=list,
        description="References to additional entities that must be in a"
        " 'success' state before this workflow can be scheduled.",
    )


class DyffEntity(Status, Labeled, SchemaVersion, DyffModelWithID):
    kind: Literal[
        "Analysis",
        "Audit",
        "AuditProcedure",
        "Challenge",
        "Curve",
        "DataSource",
        "Dataset",
        "Evaluation",
        "Family",
        "Hazard",
        "History",
        "InferenceService",
        "InferenceSession",
        "Measurement",
        "Method",
        "Model",
        "Module",
        # FIXME: (schema v1) Rename to Artifact
        "OCIArtifact",
        "Pipeline",
        "PipelineRun",
        "Report",
        "Revision",
        "SafetyCase",
        "Submission",
        "Team",
        "UseCase",
    ]

    metadata: DyffEntityMetadata = pydantic.Field(
        default_factory=DyffEntityMetadata,
        description="Entity metadata",
    )

    annotations: list[Annotation] = pydantic.Field(
        default_factory=list,
        description="A set of key-value annotations for the resource. Used to"
        " attach arbitrary non-identifying metadata to resources."
        " We follow the kubernetes annotation conventions closely.\n\n"
        " See: https://kubernetes.io/docs/concepts/overview/working-with-objects/annotations",
    )

    creationTime: datetime = pydantic.Field(
        description="Resource creation time (assigned by system)"
    )

    lastTransitionTime: Optional[datetime] = pydantic.Field(
        default=None, description="Time of last (status, reason) change."
    )

    def dependencies(self) -> list[str]:
        """List of IDs of resources that this resource depends on.

        The workflow cannot start until all dependencies have reached a success
        status. Workflows waiting for dependencies have
        ``reason = UnsatisfiedDependency``. If any dependency reaches a failure
        status, this workflow will also fail with ``reason = FailedDependency``.
        """
        return list(
            set(self._dependencies() + [e.id for e in self.metadata.preconditions])
        )

    @abc.abstractmethod
    def _dependencies(self) -> list[str]:
        """Implementations should define this function to return the data dependencies
        implied by the resource spec.

        Implementations should *not* include .metadata.preconditions in this list.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def resource_allocation(self) -> Optional[ResourceAllocation]:
        """Resource allocation required to run this workflow, if any."""
        raise NotImplementedError()


class Frameworks(str, enum.Enum):
    transformers = "transformers"


class InferenceServiceSources(str, enum.Enum):
    upload = "upload"
    build = "build"


class APIFunctions(str, enum.Enum):
    """Categories of API operations to which access can be granted."""

    consume = "consume"
    """Use the resource as a dependency in another workflow.

    Example: running an ``Evaluation`` on a ``Dataset`` requires ``consume``
    permission for the ``Dataset``.
    """

    create = "create"
    """Create a new instance of the resource.

    For resources that require uploading artifacts (such as ``Dataset``), also
    grants access to the ``upload`` and ``finalize`` endpoints.
    """

    get = "get"
    """Retrieve a single resource instance by ID."""

    query = "query"
    """Query the resource collection."""

    edit = "edit"
    """Edit properties of existing resources."""

    download = "download"
    """
    .. deprecated:: 0.5.0

        This functionality has been consolidated into ``data``.
    """

    upload = "upload"
    """
    .. deprecated:: 0.5.0

        This functionality has been consolidated into ``create``.
    """

    data = "data"
    """Download the raw data associated with the resource."""

    strata = "strata"
    """
    .. deprecated:: 0.5.0

        Similar functionality will be added in the future but with a different
        interface.
    """

    terminate = "terminate"
    """Set the resource status to ``Terminated``."""

    delete = "delete"
    """Set the resource status to ``Deleted``."""

    all = "*"


class AccessGrant(DyffSchemaBaseModel):
    """Grants access to call particular functions on particular instances of particular
    resource types.

    Access grants are **additive**; the subject of a set of grants has permission to do
    something if any part of any of those grants gives the subject that permission.
    """

    resources: list[Resources] = pydantic.Field(
        min_length=1, description="List of resource types to which the grant applies"
    )
    functions: list[APIFunctions] = pydantic.Field(
        min_length=1,
        description="List of functions on those resources to which the grant applies",
    )
    accounts: list[str] = pydantic.Field(
        default_factory=list,
        description="The access grant applies to all resources owned by the listed accounts",
    )
    entities: list[str] = pydantic.Field(
        default_factory=list,
        description="The access grant applies to all resources with IDs listed in 'entities'",
    )


class Role(DyffSchemaBaseModel):
    """A set of permissions."""

    grants: list[AccessGrant] = pydantic.Field(
        default_factory=list, description="The permissions granted to the role."
    )


class APIKey(Role):
    """A description of a Role (a set of permissions) granted to a single subject
    (either an account or a workload).

    Dyff API clients authenticate with a *token* that contains a cryptographically
    signed APIKey.
    """

    id: str = pydantic.Field(
        description="Unique ID of the resource. Maps to JWT 'jti' claim."
    )
    # TODO: Needs validator
    subject: str = pydantic.Field(
        description="Subject of access grants ('<kind>/<id>'). Maps to JWT 'sub' claim."
    )
    created: datetime = pydantic.Field(
        description="When the APIKey was created. Maps to JWT 'iat' claim."
    )
    expires: datetime = pydantic.Field(
        description="When the APIKey expires. Maps to JWT 'exp' claim."
    )
    secret: Optional[str] = pydantic.Field(
        default=None,
        description="For account keys: a secret value to check when verifying the APIKey",
    )


class Identity(DyffSchemaBaseModel):
    """The identity of an Account according to one or more external identity
    providers."""

    google: Optional[str] = pydantic.Field(default=None)


class Account(DyffSchemaBaseModel):
    """An Account in the system.

    All entities are owned by an Account.
    """

    name: str
    identity: Identity = pydantic.Field(default_factory=Identity)
    apiKeys: list[APIKey] = pydantic.Field(default_factory=list)
    # --- Added by system
    id: Optional[str] = None
    creationTime: Optional[datetime] = None


class FamilyMemberKind(str, enum.Enum):
    """The kinds of entities that can be members of a Family.

    These are resources for which it makes sense to have different versions or variants
    that evolve over time.
    """

    Dataset = "Dataset"
    InferenceService = "InferenceService"
    Method = "Method"
    Model = "Model"
    Module = "Module"


class FamilyMemberBase(DyffSchemaBaseModel):
    entity: EntityIdentifier = pydantic.Field(
        description="ID of the resource this member references.",
    )

    description: Optional[
        Annotated[str, StringConstraints(max_length=summary_maxlen())]
    ] = pydantic.Field(  # type: ignore
        default=None,
        description="A short description of the member."
        " This should describe how this version of the resource"
        " is different from other versions.",
    )


class FamilyMember(FamilyMemberBase):
    name: TagNameType = pydantic.Field(
        description="An interpretable identifier for the member that is unique"
        " in the context of the corresponding Family.",
    )

    family: str = pydantic.Field(
        description="Identifier of the Family containing this tag."
    )

    creationTime: datetime = pydantic.Field(
        description="Tag creation time (assigned by system)"
    )


class FamilyMembers(DyffSchemaBaseModel):
    members: dict[TagNameType, FamilyMember] = pydantic.Field(
        default_factory=dict,
        description="Mapping of names to IDs of member resources.",
    )


class FamilyBase(DyffSchemaBaseModel):
    memberKind: FamilyMemberKind = pydantic.Field(
        description="The kind of resource that comprises the family.",
    )


class Family(DyffEntity, FamilyBase, FamilyMembers):
    kind: Literal["Family"] = "Family"

    def _dependencies(self) -> list[str]:
        return []

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class RevisionMetadata(DyffSchemaBaseModel):
    previousRevision: Optional[str] = pydantic.Field(
        default=None,
        description="The ID of the revision from which this revision was derived."
        "If None, then this is the first revision of the entity.",
    )
    creationTime: datetime = pydantic.Field(
        description="The time when the Revision was created"
    )


class ForeignRevision(RevisionMetadata):
    id: str = pydantic.Field(description="Unique identifier of the entity")


# Note: The 'Revision' class itself is defined all the way at the end of this
# file, because OpenAPI generation doesn't work with the Python < 3.10
# "ForwardDeclaration" syntax.


class History(DyffEntity):
    kind: Literal["History"] = "History"

    historyOf: str = pydantic.Field(
        description="The ID of the entity described by this History."
    )

    latest: ForeignRevision = pydantic.Field(description="The latest Revision")
    revisions: list[ForeignRevision] = pydantic.Field(
        description="The list of known Revisions, in chronological order (newest last)."
    )


class ConcernBase(Documented):
    pass


class Concern(ConcernBase, DyffEntity):
    def label_key(self) -> str:
        return f"{Resources[self.kind].value}.dyff.io/{self.id}"

    def label_value(self) -> str:
        return "1"

    def _dependencies(self) -> list[str]:
        return []

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class Hazard(Concern):
    kind: Literal["Hazard"] = Entities.Hazard.value


class UseCase(Concern):
    kind: Literal["UseCase"] = Entities.UseCase.value


# ----------------------------------------------------------------------------


class Digest(DyffSchemaBaseModel):
    md5: Optional[str] = pydantic.Field(
        default=None, description="md5 digest of artifact data"
    )


# TODO: (schema-v1) Rename this to "File" or something -- reserve Artifact
# for OCI artifacts.
class Artifact(DyffSchemaBaseModel):
    # TODO: (schema-v1) Rename this to 'contentType' or something and commit to making it the MIME type
    kind: Optional[str] = pydantic.Field(
        default=None, description="The kind of artifact"
    )
    path: str = pydantic.Field(
        description="The relative path of the artifact within the tree"
    )
    digest: Digest = pydantic.Field(
        default_factory=Digest,
        description="One or more message digests (hashes) of the artifact data",
    )


class StorageSignedURL(DyffSchemaBaseModel):
    url: str = pydantic.Field(description="The signed URL")
    method: str = pydantic.Field(description="The HTTP method applicable to the URL")
    headers: dict[str, str] = pydantic.Field(
        default_factory=dict,
        description="Mandatory headers that must be passed with the request",
    )


class ArtifactURL(DyffSchemaBaseModel):
    artifact: Artifact
    signedURL: StorageSignedURL


class AuditRequirement(DyffSchemaBaseModel):
    """An evaluation report that must exist in order to apply an AuditProcedure."""

    dataset: str
    rubric: str


class AuditProcedure(DyffEntity):
    """An audit procedure that can be run against a set of evaluation reports."""

    kind: Literal["AuditProcedure"] = Entities.AuditProcedure.value

    name: str
    requirements: list[AuditRequirement] = pydantic.Field(default_factory=list)

    def _dependencies(self) -> list[str]:
        # Note that ``requirements`` are not "dependencies" because they don't
        # refer to a specific entity
        return []

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class Audit(DyffEntity):
    """An instance of applying an AuditProcedure to an InferenceService."""

    kind: Literal["Audit"] = Entities.Audit.value

    auditProcedure: str = pydantic.Field(description="The AuditProcedure to run.")

    inferenceService: str = pydantic.Field(description="The InferenceService to audit.")

    def _dependencies(self) -> list[str]:
        return [self.auditProcedure, self.inferenceService]

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class DataSource(DyffEntity):
    """A source of raw data from which a Dataset can be built."""

    kind: Literal["DataSource"] = Entities.DataSource.value

    name: str
    sourceKind: str
    source: Optional[str] = None

    def _dependencies(self) -> list[str]:
        return []

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class ArchiveFormat(DyffSchemaBaseModel):
    """Specification of the archives that comprise a DataSource."""

    name: str
    format: str


class ExtractorStep(DyffSchemaBaseModel):
    """Description of a step in the process of turning a hierarchical DataSource into a
    Dataset."""

    action: str
    name: Optional[str] = None
    type: Optional[str] = None


class DyffDataSchema(DyffSchemaBaseModel):
    components: list[str] = pydantic.Field(
        min_length=1,
        description="A list of named dyff data schemas. The final schema is"
        " the composition of these component schemas.",
    )
    schemaVersion: SomeSchemaVersion = pydantic.Field(
        default=SCHEMA_VERSION,  # type: ignore [arg-type]
        description="The dyff schema version",
    )

    def model_type(self) -> Type[DyffSchemaBaseModel]:
        """The composite model type."""
        return product_schema(
            named_data_schema(c, self.schemaVersion) for c in self.components
        )


class DataSchema(DyffSchemaBaseModel):
    arrowSchema: str = pydantic.Field(
        description="The schema in Arrow format, encoded with"
        " dyff.schema.arrow.encode_schema(). This is required, but can be"
        " populated from a DyffDataSchema.",
    )
    dyffSchema: Optional[DyffDataSchema] = pydantic.Field(
        default=None, description="The schema in DyffDataSchema format"
    )
    jsonSchema: Optional[dict[str, Any]] = pydantic.Field(
        default=None, description="The schema in JSON Schema format"
    )

    @staticmethod
    def from_model(model: Type[DyffSchemaBaseModel]) -> "DataSchema":
        arrowSchema = arrow.encode_schema(arrow.arrow_schema(model))
        jsonSchema = model.model_json_schema()
        return DataSchema(arrowSchema=arrowSchema, jsonSchema=jsonSchema)

    @staticmethod
    def make_input_schema(
        schema: Union[pyarrow.Schema, Type[DyffSchemaBaseModel], DyffDataSchema],
    ) -> "DataSchema":
        """Construct a complete ``DataSchema`` for inference inputs.

        This function will add required special fields for input data and then
        convert the augmented schema as necessary to populate at least the
        required ``arrowSchema`` field in the resulting ``DataSchema``.
        """
        if isinstance(schema, pyarrow.Schema):
            arrowSchema = arrow.encode_schema(arrow.make_item_schema(schema))
            return DataSchema(arrowSchema=arrowSchema)
        elif isinstance(schema, DyffDataSchema):
            item_model = make_item_type(schema.model_type())
            arrowSchema = arrow.encode_schema(arrow.arrow_schema(item_model))
            jsonSchema = item_model.model_json_schema()
            return DataSchema(
                arrowSchema=arrowSchema, dyffSchema=schema, jsonSchema=jsonSchema
            )
        else:
            item_model = make_item_type(schema)
            arrowSchema = arrow.encode_schema(arrow.arrow_schema(item_model))
            jsonSchema = item_model.model_json_schema()
            return DataSchema(arrowSchema=arrowSchema, jsonSchema=jsonSchema)

    @staticmethod
    def make_output_schema(
        schema: Union[pyarrow.Schema, Type[DyffSchemaBaseModel], DyffDataSchema],
    ) -> "DataSchema":
        """Construct a complete ``DataSchema`` for inference outputs.

        This function will add required special fields for input data and then
        convert the augmented schema as necessary to populate at least the
        required ``arrowSchema`` field in the resulting ``DataSchema``.
        """
        if isinstance(schema, pyarrow.Schema):
            arrowSchema = arrow.encode_schema(arrow.make_response_schema(schema))
            return DataSchema(arrowSchema=arrowSchema)
        elif isinstance(schema, DyffDataSchema):
            response_model = make_response_type(schema.model_type())
            arrowSchema = arrow.encode_schema(arrow.arrow_schema(response_model))
            jsonSchema = response_model.model_json_schema()
            return DataSchema(
                arrowSchema=arrowSchema, dyffSchema=schema, jsonSchema=jsonSchema
            )
        else:
            response_model = make_response_type(schema)
            arrowSchema = arrow.encode_schema(arrow.arrow_schema(response_model))
            jsonSchema = response_model.model_json_schema()
            return DataSchema(arrowSchema=arrowSchema, jsonSchema=jsonSchema)


class SchemaAdapter(DyffSchemaBaseModel):
    kind: str = pydantic.Field(
        description="Name of a schema adapter available on the platform",
    )

    configuration: Optional[dict[str, Any]] = pydantic.Field(
        default=None,
        description="Configuration for the schema adapter. Must be encodable as JSON.",
    )


class DataView(DyffSchemaBaseModel):
    id: str = pydantic.Field(description="Unique ID of the DataView")
    viewOf: str = pydantic.Field(
        description="ID of the resource that this is a view of"
    )
    schema_: DataSchema = pydantic.Field(
        alias="schema", description="Schema of the output of this view"
    )
    adapterPipeline: Optional[list[SchemaAdapter]] = pydantic.Field(
        default=None, description="Adapter pipeline to apply to produce the view"
    )


class DatasetBase(DyffSchemaBaseModel):
    name: str = pydantic.Field(description="The name of the Dataset")
    artifacts: list[Artifact] = pydantic.Field(
        min_length=1, description="Artifacts that comprise the dataset"
    )
    schema_: DataSchema = pydantic.Field(
        alias="schema", description="Schema of the dataset"
    )
    views: list[DataView] = pydantic.Field(
        default_factory=list,
        description="Available views of the data that alter its schema.",
    )


class Dataset(DyffEntity, DatasetBase):
    """An "ingested" data set in our standardized PyArrow format."""

    kind: Literal["Dataset"] = Entities.Dataset.value

    def _dependencies(self) -> list[str]:
        return []

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


# ----------------------------------------------------------------------------
# Model


class File(DyffSchemaBaseModel):
    mediaType: Optional[str] = pydantic.Field(
        default=None, description="The media type (MIME type) of the file"
    )
    path: str = pydantic.Field(
        description="The relative path of the file within the containing volume"
    )
    size: int = pydantic.Field(description="Size of the file in bytes")
    digest: Digest = pydantic.Field(
        default_factory=Digest,
        description="One or more message digests (hashes) of the file data",
    )


class FileStorageURL(DyffSchemaBaseModel):
    file: File
    signedURL: StorageSignedURL


class Volume(DyffSchemaBaseModel):
    files: list[File] = pydantic.Field(description="A list of files in the volume")


class ModelSourceKinds(str, enum.Enum):
    GitLFS = "GitLFS"
    HuggingFaceHub = "HuggingFaceHub"
    Mock = "Mock"
    OpenLLM = "OpenLLM"
    Upload = "Upload"


class ModelSourceGitLFS(DyffSchemaBaseModel):
    url: pydantic.HttpUrl = pydantic.Field(
        description="The URL of the Git LFS repository"
    )


class ModelSourceHuggingFaceHub(DyffSchemaBaseModel):
    """These arguments are forwarded to huggingface_hub.snapshot_download()"""

    repoID: str
    revision: str
    allowPatterns: Optional[list[str]] = None
    ignorePatterns: Optional[list[str]] = None


class ModelSourceOpenLLM(DyffSchemaBaseModel):
    modelKind: str = pydantic.Field(
        description="The kind of model (c.f. 'openllm build <modelKind>')"
    )

    modelID: str = pydantic.Field(
        description="The specific model identifier (c.f. 'openllm build ... --model-id <modelId>')",
    )

    modelVersion: str = pydantic.Field(
        description="The version of the model (e.g., a git commit hash)"
    )


class ModelSource(DyffSchemaBaseModel):
    kind: ModelSourceKinds = pydantic.Field(description="The kind of model source")

    gitLFS: Optional[ModelSourceGitLFS] = pydantic.Field(
        default=None, description="Specification of a Git LFS source"
    )

    huggingFaceHub: Optional[ModelSourceHuggingFaceHub] = pydantic.Field(
        default=None, description="Specification of a HuggingFace Hub source"
    )

    openLLM: Optional[ModelSourceOpenLLM] = pydantic.Field(
        default=None, description="Specification of an OpenLLM source"
    )


class AcceleratorGPU(DyffSchemaBaseModel):
    hardwareTypes: list[str] = pydantic.Field(
        min_length=1,
        description="Acceptable GPU hardware types.",
    )
    count: int = pydantic.Field(default=1, description="Number of GPUs required.")
    memory: Optional[Quantity] = pydantic.Field(
        default=None,
        description="[DEPRECATED] Amount of GPU memory required, in k8s Quantity notation",
    )


class Accelerator(DyffSchemaBaseModel):
    kind: str = pydantic.Field(
        description="The kind of accelerator; available kinds are {{GPU}}"
    )
    gpu: Optional[AcceleratorGPU] = pydantic.Field(
        default=None, description="GPU accelerator options"
    )


# FIXME: Remove .storage because it's replaced by ScratchVolume, and rename to
# ResourceRequirements for consistency with k8s.
class ModelResources(DyffSchemaBaseModel):
    storage: Optional[Quantity] = pydantic.Field(
        default=None,
        deprecated=True,
        description="Storage required for packaged model, in k8s Quantity notation",
    )

    memory: Optional[Quantity] = pydantic.Field(
        default=None,
        description="Memory, in k8s Quantity notation",
    )

    cpu: Optional[Quantity] = pydantic.Field(
        default=None,
        description="Number of CPUs, in k8s Quantity notation",
    )


class ModelStorageMedium(str, enum.Enum):
    Mock = "Mock"
    ObjectStorage = "ObjectStorage"
    PersistentVolume = "PersistentVolume"
    FUSEVolume = "FUSEVolume"


class ModelArtifactKind(str, enum.Enum):
    HuggingFaceCache = "HuggingFaceCache"
    Mock = "Mock"
    Volume = "Volume"


class ModelArtifactHuggingFaceCache(DyffSchemaBaseModel):
    repoID: str = pydantic.Field(
        description="Name of the model in the HuggingFace cache"
    )
    revision: str = pydantic.Field(description="Model revision")

    def snapshot_path(self) -> str:
        return f"models--{self.repoID.replace('/', '--')}/snapshots/{self.revision}"


class ModelArtifact(DyffSchemaBaseModel):
    kind: ModelArtifactKind = pydantic.Field(
        description="How the model data is represented"
    )
    huggingFaceCache: Optional[ModelArtifactHuggingFaceCache] = pydantic.Field(
        default=None, description="Model stored in a HuggingFace cache"
    )
    volume: Optional[Volume] = pydantic.Field(
        default=None, description="Model stored as a generic volume"
    )


class ModelStorage(DyffSchemaBaseModel):
    medium: ModelStorageMedium = pydantic.Field(description="Storage medium")


class ModelBase(DyffSchemaBaseModel):
    name: str = pydantic.Field(description="The name of the Model.")

    artifact: ModelArtifact = pydantic.Field(
        description="How the model data is represented"
    )

    storage: Optional[ModelStorage] = pydantic.Field(
        default=None,
        description="How the model data is stored",
        deprecated="Specifics of the storage engine are an implementation detail.",
    )


class ModelSpec(ModelBase):
    source: ModelSource = pydantic.Field(
        description="Source from which the model artifact was obtained"
    )

    resources: ModelResources = pydantic.Field(
        description="Resource requirements of the model."
    )

    accelerators: Optional[list[Accelerator]] = pydantic.Field(
        default=None,
        description="Accelerator hardware that is compatible with the model.",
    )


class Model(DyffEntity, ModelSpec):
    """A Model is the "raw" form of an inference model, from which one or more
    InferenceServices may be built."""

    kind: Literal["Model"] = Entities.Model.value

    def _dependencies(self) -> list[str]:
        return []

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class InferenceServiceBuilder(DyffSchemaBaseModel):
    kind: str
    args: Optional[list[str]] = None


class InferenceServiceRunnerKind(str, Enum):
    BENTOML_SERVICE_OPENLLM = "bentoml_service_openllm"
    CONTAINER = "container"
    HUGGINGFACE = "huggingface"
    MOCK = "mock"
    STANDALONE = "standalone"
    VLLM = "vllm"


class ContainerImageSource(DyffSchemaBaseModel):
    host: str = pydantic.Field(description="The host of the container image registry.")
    name: str = pydantic.Field(
        description="The name of the image",
        # https://github.com/opencontainers/distribution-spec/blob/main/spec.md#pull
        pattern=r"^[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*(\/[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*)*$",
    )
    digest: str = pydantic.Field(
        description="The digest of the image. The image is always pulled by"
        " digest, even if 'tag' is specified.",
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    tag: Optional[TagNameType] = pydantic.Field(
        default=None,
        description="The tag of the image. Although the image is always pulled"
        " by digest, including the tag is strongly recommended as it is often"
        " the main source of versioning information.",
    )

    def url(self) -> str:
        return f"{self.host}/{self.name}@{self.digest}"

    @pydantic.field_validator("host")
    def validate_host(cls, v: str):
        if "/" in v:
            raise ValueError(
                "host: slashes not allowed; do not specify a scheme or path"
            )
        if "_" in v:
            # https://docs.docker.com/reference/cli/docker/image/tag/#description
            raise ValueError(
                "host: image registry hostnames may not contain underscores"
            )

        # This works because we know there are no slashes in the value
        # "Following the syntax specifications in RFC 1808, urlparse recognizes
        # a netloc only if it is properly introduced by ‘//’. Otherwise the
        # input is presumed to be a relative URL and thus to start with a path
        # component."
        # https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse
        parsed = urllib.parse.urlparse(f"//{v}")
        if (
            parsed.scheme
            or parsed.path
            or parsed.params
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "host: must be 'hostname' or 'hostname:port', and nothing else"
            )

        return v


class EnvVar(DyffSchemaBaseModel):
    name: str
    value: str


# TODO: ModelResources is deprecated
ResourceRequirements = ModelResources


class VolumeMountKind(str, enum.Enum):
    data = "Data"
    scratch = "Scratch"


class VolumeMountData(DyffSchemaBaseModel):
    source: EntityIdentifier = pydantic.Field(
        description="The Dyff platform resource to mount."
        " Must be a volume-like entity such as a Model or Dataset."
    )


class VolumeMountScratch(DyffSchemaBaseModel):
    capacity: Quantity = pydantic.Field(
        description="Minimum storage capacity of the Scratch volume."
    )


class VolumeMount(DyffSchemaBaseModel):
    kind: VolumeMountKind = pydantic.Field(description="The kind of volume mount.")
    name: str = pydantic.Field(description="A descriptive name for the mount.")
    mountPath: Path = pydantic.Field(
        description="Where to mount the volume in the running container."
        " Must be an absolute path."
    )
    data: Optional[VolumeMountData] = pydantic.Field(
        default=None, description="Configuration for Data volume mounts."
    )
    scratch: Optional[VolumeMountScratch] = pydantic.Field(
        default=None, description="Configuration for Scratch volume mounts."
    )

    @pydantic.model_validator(mode="after")
    def _validate_kind_matches_payload(self):
        """Ensure payload fields match declared kind."""
        if self.kind == VolumeMountKind.data:
            if self.data is None or self.scratch is not None:
                raise ValueError(
                    "VolumeMount(kind='Data') requires .data and forbids .scratch"
                )
        elif self.kind == VolumeMountKind.scratch:
            if self.scratch is None or self.data is not None:
                raise ValueError(
                    "VolumeMount(kind='Scratch') requires .scratch and forbids .data"
                )
        return self


class Container(DyffSchemaBaseModel):
    """Configuration of a runnable container backed by either an image hosted in an
    external registyr, or an image artifact hosted in the Dyff system.

    This is mostly a subset of the Kubernetes Container schema.
    """

    args: Optional[list[str]] = pydantic.Field(
        default=None,
        description="Arguments to the entrypoint."
        " The container image's CMD is used if this is not provided.",
    )
    command: Optional[list[str]] = pydantic.Field(
        default=None,
        description="Entrypoint array. Not executed within a shell."
        " The container image's ENTRYPOINT is used if this is not provided.",
    )
    env: Optional[list[EnvVar]] = pydantic.Field(
        default=None,
        description="List of environment variables to set in the container.",
    )
    # TODO: (DYFF-421) Make .image required
    image: Optional[ContainerImageSource] = pydantic.Field(
        default=None,
        description="The container image that implements the runner."
        " Exactly one of .image and .imageRef must be set.",
    )
    imageRef: Optional[EntityIdentifier] = pydantic.Field(
        default=None,
        description="Container image reference. Must be an image artifact"
        " that has been uploaded to this Dyff instance and is in Ready status."
        " Exactly one of .image and .imageRef must be set.",
    )
    resources: ResourceRequirements = pydantic.Field(
        description="Compute Resources required by this container."
    )
    volumeMounts: Optional[list[VolumeMount]] = pydantic.Field(
        default=None, description="Volumes to mount into the container's filesystem."
    )
    workingDir: Optional[Path] = pydantic.Field(
        default=None,
        description="Container's working directory. If not specified,"
        " the container runtime's default will be used,"
        " which might be configured in the container image.",
    )


class InferenceServiceRunner(Container):
    """Configuration of the runtime environment to use to run an inference service.

    You can run the service in an arbitrary Docker container by using
    ``.kind == "container" and setting ``.imageRef`` to a container image that
    has been uploaded to Dyff using the ``/artifacts/create`` API.

    Other runner kinds are "managed" runners that are maintained as part of the
    Dyff project. Using a managed runner simplifies the configuration of
    inference services backed by models in common formats, such as HuggingFace models.
    """

    kind: InferenceServiceRunnerKind

    accelerator: Optional[Accelerator] = pydantic.Field(
        default=None, description="Optional accelerator hardware to use, per node."
    )

    nodes: int = pydantic.Field(
        default=1,
        ge=1,
        description="Number of nodes. The resource specs apply to *each node*.",
    )


class InferenceInterface(DyffSchemaBaseModel):
    endpoint: str = pydantic.Field(description="HTTP endpoint for inference.")

    outputSchema: DataSchema = pydantic.Field(
        description="Schema of the inference outputs.",
    )

    inputPipeline: Optional[list[SchemaAdapter]] = pydantic.Field(
        default=None, description="Input adapter pipeline."
    )

    outputPipeline: Optional[list[SchemaAdapter]] = pydantic.Field(
        default=None, description="Output adapter pipeline."
    )


class ForeignModel(DyffModelWithID, ModelBase):
    pass


class InferenceServiceBase(DyffSchemaBaseModel):
    name: str = pydantic.Field(description="The name of the service.")

    builder: Optional[InferenceServiceBuilder] = pydantic.Field(
        default=None,
        description="Configuration of the Builder used to build the service.",
    )

    # FIXME: (DYFF-261) .runner should be required
    runner: Optional[InferenceServiceRunner] = pydantic.Field(
        default=None,
        description="Configuration of the managed runner used to run the service.",
    )

    interface: InferenceInterface = pydantic.Field(
        description="How to move data in and out of the service."
    )

    outputViews: list[DataView] = pydantic.Field(
        default_factory=list,
        description="Views of the output data for different purposes.",
    )


class InferenceServiceSpec(InferenceServiceBase):
    model: Optional[ForeignModel] = pydantic.Field(
        default=None,
        description="The Model backing this InferenceService, if applicable.",
    )


class InferenceService(DyffEntity, InferenceServiceSpec):
    """An InferenceService is an inference model packaged as a Web service."""

    kind: Literal["InferenceService"] = Entities.InferenceService.value

    def _dependencies(self) -> list[str]:
        result = []
        if self.model is not None:
            result.append(self.model.id)
        return result

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class ForeignInferenceService(DyffModelWithID, InferenceServiceSpec):
    pass


class InferenceSessionBase(DyffSchemaBaseModel):
    expires: Optional[datetime] = pydantic.Field(
        default=None,
        description="Expiration time for the session. Use of this field is recommended to avoid accidental compute costs.",
    )

    replicas: int = pydantic.Field(default=1, description="Number of model replicas")

    accelerator: Optional[Accelerator] = pydantic.Field(
        default=None, description="Accelerator hardware to use, per node."
    )

    useSpotPods: bool = pydantic.Field(
        default=True,
        description="Use preemptible 'spot pods' for cheaper computation."
        " Note that some accelerator types may not be available in non-spot pods.",
    )


class InferenceSessionSpec(InferenceSessionBase):
    inferenceService: ForeignInferenceService = pydantic.Field(
        description="InferenceService ID"
    )


class InferenceSession(DyffEntity, InferenceSessionSpec):
    """An InferenceSession is a deployment of an InferenceService that exposes an API
    for interactive queries."""

    kind: Literal["InferenceSession"] = Entities.InferenceSession.value

    securityContext: SecurityContext = pydantic.Field(
        default_factory=SecurityContext,
        description="Security-related properties of the entity.",
    )

    def _dependencies(self) -> list[str]:
        return [self.inferenceService.id]

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class InferenceSessionAndToken(DyffSchemaBaseModel):
    inferencesession: InferenceSession
    token: str


class InferenceSessionReference(DyffSchemaBaseModel):
    session: str = pydantic.Field(
        description="The ID of a running inference session.",
    )

    interface: InferenceInterface = pydantic.Field(
        description="How to move data in and out of the service."
    )


class DatasetFilter(DyffSchemaBaseModel):
    """A rule for restrcting which instances in a Dataset are returned."""

    field: str
    relation: str
    value: str


class TaskSchema(DyffSchemaBaseModel):
    # InferenceServices must consume a *subset* of this schema
    input: DataSchema
    # InferenceServices must output a *superset* of this schema
    output: DataSchema
    # This will be an enumerated tag specifying task semantics (e.g., Classification, TextGeneration)
    objective: str


class EvaluationClientConfiguration(DyffSchemaBaseModel):
    badRequestPolicy: Literal["Abort", "Skip"] = pydantic.Field(
        default="Abort",
        description="What to do if an inference call raises a 400 Bad Request"
        " or a similar error that indicates a problem with the input instance."
        " Abort (default): the evaluation fails immediately."
        " Skip: output None for the bad instance and continue.",
    )

    transientErrorRetryLimit: int = pydantic.Field(
        default=120,
        ge=0,
        description="How many times to retry transient errors before the"
        " evaluation fails. The count is reset after a successful inference."
        " Note that transient errors often occur during inference service"
        " startup. The maximum time that the evaluation will wait for a"
        " service (re)start is (retry limit) * (retry delay).",
    )

    transientErrorRetryDelaySeconds: int = pydantic.Field(
        default=30,
        ge=1,
        description="How long to wait before retrying a transient error."
        " Note that transient errors often occur during inference service"
        " startup. The maximum time that the evaluation will wait for a"
        " service (re)start is (retry limit) * (retry delay).",
    )

    duplicateOutputPolicy: Literal["Deduplicate", "Error", "Ignore"] = pydantic.Field(
        default="Deduplicate",
        description="What to do if there are missing outputs."
        " Deduplicate (default): output only one of the duplicates, chosen"
        " arbitrarily. Error: the evaluation fails. Ignore: duplicates are"
        " retained in the output."
        " Setting this to Error is discouraged because duplicates can"
        " arise in normal operation if the client restarts due to"
        " a transient failure.",
    )

    missingOutputPolicy: Literal["Error", "Ignore"] = pydantic.Field(
        default="Error",
        description="What to do if there are missing outputs."
        " Error (default): the evaluation fails. Ignore: no error.",
    )

    requestTimeoutSeconds: int = pydantic.Field(
        default=30, ge=0, description="The timeout delay for requests."
    )


class EvaluationInferenceSessionRequest(InferenceSessionBase):
    inferenceService: str = pydantic.Field(description="InferenceService ID")


class EvaluationBase(DyffSchemaBaseModel):
    dataset: str = pydantic.Field(description="The Dataset to evaluate on.")

    replications: int = pydantic.Field(
        default=1, description="Number of replications to run."
    )

    # TODO: This should be in the client config object
    workersPerReplica: Optional[int] = pydantic.Field(
        default=None,
        description="Number of data workers per inference service replica.",
    )

    client: EvaluationClientConfiguration = pydantic.Field(
        default_factory=EvaluationClientConfiguration,
        description="Configuration for the evaluation client.",
    )


class EvaluationRequestBase(EvaluationBase):
    """A description of how to run an InferenceService on a Dataset to obtain a set of
    evaluation results."""

    inferenceSession: Optional[EvaluationInferenceSessionRequest] = pydantic.Field(
        default=None,
        description="Specification of the InferenceSession that will perform inference for the evaluation.",
    )

    inferenceSessionReference: Optional[str] = pydantic.Field(
        default=None,
        description="The ID of a running inference session that will be used"
        " for the evaluation, instead of starting a new one.",
    )

    @pydantic.model_validator(mode="after")
    def check_session_exactly_one(self):
        session = self.inferenceSession is not None
        session_ref = self.inferenceSessionReference is not None
        if not (session ^ session_ref):
            raise ValueError(
                "must specify exactly one of {inferenceSession, inferenceSessionReference}"
            )
        return self


class Evaluation(DyffEntity, EvaluationBase):
    """A description of how to run an InferenceService on a Dataset to obtain a set of
    evaluation results."""

    kind: Literal["Evaluation"] = Entities.Evaluation.value

    inferenceSession: InferenceSessionSpec = pydantic.Field(  # type: ignore[assignment]
        description="Specification of the InferenceSession that will perform"
        " inference for the evaluation.",
    )

    inferenceSessionReference: Optional[str] = pydantic.Field(
        default=None,
        description="ID of a running inference session that will be used"
        " for the evaluation instead of starting a new one.",
    )

    securityContext: SecurityContext = pydantic.Field(
        default_factory=SecurityContext,
        description="Security-related properties of the entity.",
    )

    def _dependencies(self) -> list[str]:
        # TODO: It would be nice if the session could be a dependency,
        # so that the client doesn't start until the session is ready, but
        # dyff-orchestrator can't handle dependencies on sessions currently.
        return [self.dataset, self.inferenceSession.inferenceService.id]

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class ModuleBase(DyffSchemaBaseModel):
    name: str = pydantic.Field(description="The name of the Module")
    artifacts: list[Artifact] = pydantic.Field(
        min_length=1, description="Artifacts that comprise the Module implementation"
    )


class Module(DyffEntity, ModuleBase):
    """An extension module that can be loaded into Report workflows."""

    kind: Literal["Module"] = Entities.Module.value

    def _dependencies(self) -> list[str]:
        return []

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class ReportBase(DyffSchemaBaseModel):
    rubric: str = pydantic.Field(
        description="The scoring rubric to apply (e.g., 'classification.TopKAccuracy').",
    )

    evaluation: str = pydantic.Field(
        description="The evaluation (and corresponding output data) to run the report on."
    )

    modules: list[str] = pydantic.Field(
        default_factory=list,
        description="Additional modules to load into the report environment",
    )


class Report(DyffEntity, ReportBase):
    """A Report transforms raw model outputs into some useful statistics.

    .. deprecated:: 0.8.0

        Report functionality has been refactored into the
        Method/Measurement/Analysis apparatus. Creation of new Reports is
        disabled.
    """

    kind: Literal["Report"] = Entities.Report.value

    dataset: str = pydantic.Field(description="The input dataset.")

    inferenceService: str = pydantic.Field(
        description="The inference service used in the evaluation"
    )

    model: Optional[str] = pydantic.Field(
        default=None,
        description="The model backing the inference service, if applicable",
    )

    datasetView: Optional[DataView] = pydantic.Field(
        default=None,
        description="View of the input dataset required by the report (e.g., ground-truth labels).",
    )

    evaluationView: Optional[DataView] = pydantic.Field(
        default=None,
        description="View of the evaluation output data required by the report.",
    )

    def _dependencies(self) -> list[str]:
        return [self.evaluation] + self.modules

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class QueryableDyffEntity(DyffSchemaBaseModel):
    id: str = pydantic.Field(description="Unique identifier of the entity")
    name: str = pydantic.Field(description="Descriptive name of the resource")


class MeasurementLevel(str, enum.Enum):
    Dataset = "Dataset"
    Instance = "Instance"


class AnalysisOutputQueryFields(DyffSchemaBaseModel):
    analysis: Optional[str] = pydantic.Field(
        default=None,
        description="ID of the Analysis that produced the output.",
    )

    method: QueryableDyffEntity = pydantic.Field(
        description="Identifying information about the Method that was run to produce the output."
    )

    inputs: Optional[list[str]] = pydantic.Field(
        default=None,
        description="IDs of resources that were inputs to the Analysis.",
    )


class MeasurementSpec(DyffSchemaBaseModel):
    name: str = pydantic.Field(description="Descriptive name of the Measurement.")
    description: Optional[str] = pydantic.Field(
        default=None, description="Long-form description, interpreted as Markdown."
    )
    level: MeasurementLevel = pydantic.Field(description="Measurement level")
    schema_: DataSchema = pydantic.Field(
        alias="schema",
        description="Schema of the measurement data. Instance-level measurements must include an _index_ field.",
    )


class SafetyCaseSpec(DyffSchemaBaseModel):
    name: str = pydantic.Field(description="Descriptive name of the SafetyCase.")
    description: Optional[str] = pydantic.Field(
        default=None, description="Long-form description, interpreted as Markdown."
    )


class MethodImplementationKind(str, enum.Enum):
    JupyterNotebook = "JupyterNotebook"
    PythonFunction = "PythonFunction"

    PythonRubric = "PythonRubric"
    """A Rubric generates an instance-level measurement, consuming a Dataset and an
    Evaluation.

    .. deprecated:: 0.8.0

        Report functionality has been refactored into the
        Method/Measurement/Analysis apparatus. Creation of new Reports is
        disabled.
    """


class MethodImplementationJupyterNotebook(DyffSchemaBaseModel):
    notebookModule: str = pydantic.Field(
        description="ID of the Module that contains the notebook file."
        " This does *not* add the Module as a dependency; you must do that separately."
    )
    notebookPath: str = pydantic.Field(
        description="Path to the notebook file relative to the Module root directory."
    )


class MethodImplementationPythonFunction(DyffSchemaBaseModel):
    fullyQualifiedName: str = pydantic.Field(
        description="The fully-qualified name of the Python function to call."
    )


class MethodImplementationPythonRubric(DyffSchemaBaseModel):
    """A Rubric generates an instance-level measurement, consuming a Dataset and an
    Evaluation.

    .. deprecated:: 0.8.0

        Report functionality has been refactored into the
        Method/Measurement/Analysis apparatus. Creation of new Reports is
        disabled.
    """

    fullyQualifiedName: str = pydantic.Field(
        description="The fully-qualified name of the Python Rubric to run."
    )


class MethodImplementation(DyffSchemaBaseModel):
    kind: str = pydantic.Field(description="The kind of implementation")
    pythonFunction: Optional[MethodImplementationPythonFunction] = pydantic.Field(
        default=None, description="Specification of a Python function to call."
    )
    pythonRubric: Optional[MethodImplementationPythonRubric] = pydantic.Field(
        default=None, description="@deprecated Specification of a Python Rubric to run."
    )
    jupyterNotebook: Optional[MethodImplementationJupyterNotebook] = pydantic.Field(
        default=None, description="Specification of a Jupyter notebook to run."
    )


class MethodInputKind(str, enum.Enum):
    Dataset = Entities.Dataset.value
    Evaluation = Entities.Evaluation.value
    Measurement = Entities.Measurement.value

    Report = Entities.Report.value
    """
    .. deprecated:: 0.8.0

        The Report entity is deprecated, but we accept it as an analysis input
        for backward compatibility.
    """


class MethodOutputKind(str, enum.Enum):
    Measurement = Entities.Measurement.value
    SafetyCase = Entities.SafetyCase.value


class MethodParameter(DyffSchemaBaseModel):
    keyword: str = pydantic.Field(
        description="The parameter is referred to by 'keyword' in the context of the method implementation."
    )
    description: Optional[str] = pydantic.Field(
        default=None, description="Long-form description, interpreted as Markdown."
    )


class MethodInput(DyffSchemaBaseModel):
    kind: MethodInputKind = pydantic.Field(description="The kind of input artifact.")
    keyword: str = pydantic.Field(
        description="The input is referred to by 'keyword' in the context of the method implementation."
    )
    description: Optional[str] = pydantic.Field(
        default=None, description="Long-form description, interpreted as Markdown."
    )


class MethodOutput(DyffSchemaBaseModel):
    kind: MethodOutputKind = pydantic.Field(description="The kind of output artifact")
    measurement: Optional[MeasurementSpec] = pydantic.Field(
        default=None, description="Specification of a Measurement output."
    )
    safetyCase: Optional[SafetyCaseSpec] = pydantic.Field(
        default=None, description="Specification of a SafetyCase output."
    )


class MethodScope(str, enum.Enum):
    InferenceService = Entities.InferenceService.value
    Evaluation = Entities.Evaluation.value


class ScoreSpec(DyffSchemaBaseModel):
    name: str = pydantic.Field(
        description="The name of the score. Used as a key for retrieving score data."
        " Must be unique within the Method context.",
        pattern=identifier_regex(),
        max_length=identifier_maxlen(),
    )

    title: str = pydantic.Field(
        description="The title text to use when displaying score information.",
        max_length=title_maxlen(),
    )

    summary: str = pydantic.Field(
        description="A short text description of what the score measures.",
        max_length=summary_maxlen(),
    )

    valence: Literal["positive", "negative", "neutral"] = pydantic.Field(
        default="neutral",
        description="A score has 'positive' valence if 'more is better',"
        " 'negative' valence if 'less is better', and 'neutral' valence if"
        " 'better' is not meaningful for this score.",
    )

    priority: Literal["primary", "secondary"] = pydantic.Field(
        default="primary",
        description="The 'primary' score will be displayed in any UI widgets"
        " that expect a single score. There must be exactly 1 primary score.",
    )

    minimum: Optional[float] = pydantic.Field(
        default=None, description="The minimum possible value, if known."
    )

    maximum: Optional[float] = pydantic.Field(
        default=None, description="The maximum possible value, if known."
    )

    format: str = pydantic.Field(
        default="{quantity:.1f}",
        # Must use the 'quantity' key in the format string:
        # (Maybe string not ending in '}')(something like '{quantity:f}')(maybe another string)
        pattern=r"^(.*[^{])?[{]quantity(:[^}]*)?[}]([^}].*)?$",
        description="A Python 'format' string describing how to render the score"
        " as a string. You *must* use the keyword 'quantity' in the format"
        " string, and you may use 'unit' as well (e.g., '{quantity:.2f} {unit}')."
        " It is *strongly recommended* that you limit the output precision"
        " appropriately; use ':.0f' for integer-valued scores.",
    )

    unit: Optional[str] = pydantic.Field(
        default=None,
        description="The unit of measure, if applicable (e.g., 'meters', 'kJ/g')."
        " Use standard SI abbreviations where possible for better indexing.",
    )

    def quantity_string(self, quantity: float) -> str:
        """Formats the given quantity as a string, according to the formatting
        information stored in this ScoreSpec."""
        return self.format_quantity(self.format, quantity, unit=self.unit)

    @pydantic.model_validator(mode="after")
    def _validate_minimum_maximum(self):
        minimum = self.minimum
        maximum = self.maximum
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError(f"minimum {minimum} is greater than maximum {maximum}")
        return self

    @pydantic.field_validator("format")
    def _validate_format(cls, v):
        x = cls.format_quantity(v, 3.14, unit="kg")
        y = cls.format_quantity(v, -2.03, unit="kg")
        if x == y:
            # Formatted results for different quantities should be different
            raise ValueError("format string does not mention 'quantity'")

        return v

    @classmethod
    def format_quantity(
        cls, format: str, quantity: float, *, unit: Optional[str] = None
    ) -> str:
        return format.format(quantity=quantity, unit=unit)


class CurveSpec(DyffSchemaBaseModel):
    """Metadata describing the curve dimensions and how to read them.

    - `dimensions` supplies per-dimension metadata (name -> ScoreSpec).
    - Use these keys as columns in `CurveData.points`.
    """

    name: str = pydantic.Field(
        description="Unique key for this curve within the Method context.",
        pattern=identifier_regex(),
        max_length=identifier_maxlen(),
    )
    title: str = pydantic.Field(
        description="Human-friendly title for the curve.",
        max_length=title_maxlen(),
    )
    summary: str = pydantic.Field(
        description="Short description of what the curve shows.",
        max_length=summary_maxlen(),
    )
    dimensions: dict[str, ScoreSpec] = pydantic.Field(
        description=(
            "Per-dimension metadata. Keys must match the columns stored in CurveData.points. "
            "Typical keys might include 'x', 'y', 'threshold', 'tp', 'fp', etc."
        )
    )


class MethodBase(DyffSchemaBaseModel):
    name: str = pydantic.Field(description="Descriptive name of the Method.")

    scope: MethodScope = pydantic.Field(
        description="The scope of the Method. The Method produces outputs that"
        " are specific to one entity of the type specified in the .scope field."
    )

    description: Optional[str] = pydantic.Field(
        default=None, description="Long-form description, interpreted as Markdown."
    )

    implementation: MethodImplementation = pydantic.Field(
        description="How the Method is implemented."
    )

    parameters: list[MethodParameter] = pydantic.Field(
        default_factory=list,
        description="Configuration parameters accepted by the Method. Values are available at ctx.args(keyword)",
    )

    inputs: list[MethodInput] = pydantic.Field(
        default_factory=list,
        description="Input data entities consumed by the Method. Available at ctx.inputs(keyword)",
    )

    output: MethodOutput = pydantic.Field(
        description="Specification of the Method output."
    )

    scores: list[Union[ScoreSpec, CurveSpec]] = pydantic.Field(
        default_factory=list,
        description="Specifications of the Scores that this Method produces.",
    )

    modules: list[str] = pydantic.Field(
        default_factory=list,
        description="Modules to load into the analysis environment",
    )

    analysisImage: Optional[ContainerImageSource] = pydantic.Field(
        default=None,
        description="Optional container image to use for running analysis methods."
        " If specified, analysis will run in this custom container instead of"
        " the default analysis environment.",
    )

    @pydantic.field_validator("scores")
    def _scores_validator(cls, scores):
        score_specs = [s for s in scores if isinstance(s, ScoreSpec)]
        if score_specs:
            primary_count = sum(s.priority == "primary" for s in score_specs)
            if primary_count != 1:
                raise ValueError(
                    "scores: Must have exactly one primary ScoreSpec (curves excluded)"
                )
        return scores


class MethodMetadata(Metadata):
    concerns: list[Concern] = pydantic.Field(
        default_factory=list, description="The Concerns applicable to this Method."
    )


class ModelMetadata(Metadata):
    pass


class Method(DyffEntity, MethodBase):
    kind: Literal["Method"] = Entities.Method.value

    def _dependencies(self) -> list[str]:
        return self.modules

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class EntityIDMarker:
    """Marker class to indicate that a field contains an entity ID that supports
    family@tag resolution."""


# Type alias for entity ID fields that support family@tag resolution
EntityIDField: TypeAlias = Annotated[str, EntityIDMarker]


class AnalysisInput(DyffSchemaBaseModel):
    keyword: str = pydantic.Field(
        description="The 'keyword' specified for this input in the MethodSpec."
    )
    entity: EntityIDField = pydantic.Field(
        description="The ID of the entity whose data should be made available as 'keyword'."
    )


class AnalysisArgument(DyffSchemaBaseModel):
    keyword: str = pydantic.Field(
        description="The 'keyword' of the corresponding ModelParameter."
    )
    value: str = pydantic.Field(
        description="The value of of the argument."
        " Always a string; implementations are responsible for parsing."
    )


class ForeignMethod(DyffModelWithID, MethodBase):
    pass


class AnalysisScope(DyffSchemaBaseModel):
    """The specific entities to which the analysis applies.

    When applying an InferenceService-scoped Method, at least
    ``.inferenceService`` must be set.

    When applying an Evaluation-scoped Method, at least ``.evaluation``,
    ``.inferenceService``, and ``.dataset`` must be set.
    """

    dataset: Optional[str] = pydantic.Field(
        default=None, description="The Dataset to which the analysis applies."
    )
    inferenceService: Optional[str] = pydantic.Field(
        default=None, description="The InferenceService to which the analysis applies."
    )
    evaluation: Optional[str] = pydantic.Field(
        default=None, description="The Evaluation to which the analysis applies."
    )
    model: Optional[str] = pydantic.Field(
        default=None, description="The Model to which the analysis applies."
    )


class AnalysisBase(DyffSchemaBaseModel):
    scope: AnalysisScope = pydantic.Field(
        default_factory=AnalysisScope,
        description="The specific entities to which the analysis results apply."
        " At a minimum, the field corresponding to method.scope must be set.",
    )

    arguments: list[AnalysisArgument] = pydantic.Field(
        default_factory=list,
        description="Arguments to pass to the Method implementation.",
    )

    inputs: list[AnalysisInput] = pydantic.Field(
        default_factory=list, description="Mapping of keywords to data entities."
    )


class AnalysisRequestBase(AnalysisBase):
    method: EntityIDField = pydantic.Field(description="Method ID")


class AnalysisData(DyffSchemaBaseModel):
    """Arbitrary additional data for the Analysis, specified as a key-value pair where
    the value is the data encoded in base64."""

    key: str = pydantic.Field(
        description="Key identifying the data. For data about a Dyff entity,"
        " this should be the entity's ID."
    )

    value: str = pydantic.Field(
        # Canonical base64 encoding
        # https://stackoverflow.com/a/64467300/3709935
        pattern=r"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?$",
        description="Arbitrary data encoded in base64.",
    )


class Analysis(AnalysisBase):
    method: ForeignMethod = pydantic.Field(
        description="The analysis Method to run.",
    )

    data: list[AnalysisData] = pydantic.Field(
        default_factory=list, description="Additional data to supply to the analysis."
    )

    securityContext: SecurityContext = pydantic.Field(
        default_factory=SecurityContext,
        description="Security-related properties of the entity.",
    )


class Measurement(DyffEntity, MeasurementSpec, Analysis):
    kind: Literal["Measurement"] = Entities.Measurement.value

    def _dependencies(self) -> list[str]:
        return [self.method.id] + [x.entity for x in self.inputs]

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class SafetyCase(DyffEntity, SafetyCaseSpec, Analysis):
    kind: Literal["SafetyCase"] = Entities.SafetyCase.value

    def _dependencies(self) -> list[str]:
        return [self.method.id] + [x.entity for x in self.inputs]

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class ScoreMetadataRefs(AnalysisScope):
    """References to other Dyff entities related to a Score."""

    method: str = pydantic.Field(description="The Method that generates the score.")


class ScoreMetadata(DyffSchemaBaseModel):
    """Metadata about a Score entity."""

    refs: ScoreMetadataRefs = pydantic.Field(
        description="References to other related Dyff entities."
    )


class ScoreData(ScoreSpec):
    """ScoreData is an "instance" of a ScoreSpec containing the concrete measured value
    for the score."""

    metadata: ScoreMetadata = pydantic.Field(
        description="Metadata about the score; used for indexing.",
    )

    analysis: str = pydantic.Field(
        description="The Analysis that generated the current score instance."
    )

    quantity: float | None = pydantic.Field(
        default=None, description="Numeric quantity for scalar scores."
    )
    points: dict[str, list[float]] | None = pydantic.Field(
        default=None,
        description="Aligned vectors for curve scores. Keys should match curve.dimensions.",
    )

    quantityString: str = pydantic.Field(
        description="Formatted string representation of .quantity (scalar) or a summary string (curve)."
    )
    text: str = pydantic.Field(
        description="Short text description of what the value/curve means.",
        max_length=summary_maxlen(),
    )


class Score(ScoreData):
    """A Score is a numeric quantity describing an aspect of system performance.

    Conceptually, a Score is an "instance" of a ScoreSpec.
    """

    kind: Literal["Score"] = Entities.Score.value

    id: str = pydantic.Field(description="Unique identifier of the entity")


class CurveData(CurveSpec):
    """An instance of a curve produced by an analysis.

    - Inherits the curve spec (name/title/summary/dimensions) directly.
    - `points` is a dict-of-lists: each key is a dimension name defined in `dimensions`.
    - All lists must be the same (non-zero) length.

    spec: CurveSpec = pydantic.Field(description="The CurveSpec this data conforms to.")
    """

    metadata: ScoreMetadata = pydantic.Field(
        description="Indexing metadata (method required).",
    )
    analysis: str = pydantic.Field(
        description="ID of the Analysis that produced this curve."
    )
    points: dict[str, list[float]] = pydantic.Field(
        description="Aligned vectors for each dimension; all lists must have equal length >= 1."
    )

    @pydantic.model_validator(mode="after")
    def _validate_points(self):
        if not self.points:
            raise ValueError("CurveData.points must not be empty")

        lengths = {k: len(v) for k, v in self.points.items()}
        uniq = set(lengths.values())
        if len(uniq) != 1:
            raise ValueError(
                f"All vectors must have equal length; got lengths {lengths}"
            )
        n = next(iter(uniq))
        if n < 1:
            raise ValueError("Vectors must contain at least 1 point")

        missing = [k for k in self.dimensions.keys() if k not in self.points]
        if missing:
            raise ValueError(f"points is missing required dimensions: {missing}")
        return self


class Curve(CurveData):
    kind: Literal["Curve"] = Entities.Curve.value

    id: str = pydantic.Field(description="Unique identifier of the entity")


# ---------------------------------------------------------------------------
# OCI artifacts


# TODO: (schema-v1) Rename this to Artifact
class OCIArtifact(DyffEntity):
    kind: Literal["OCIArtifact"] = Entities.Artifact.value

    def _dependencies(self) -> list[str]:
        return []

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


# ----------------------------------------------------------------------------
# Challenges


class ChallengeContentPage(DyffSchemaBaseModel):
    """The content for the Web page corresponding to a challenge or challenge-related
    object."""

    title: str = pydantic.Field(
        default="Untitled Challenge",
        description='A short plain string suitable as a title or "headline".',
        max_length=title_maxlen(),
    )

    summary: str = pydantic.Field(
        default="",
        description="A brief summary, suitable for display in small UI elements.",
        max_length=summary_maxlen(),
    )

    body: str = pydantic.Field(
        default="",
        description="Long-form documentation. Interpreted as"
        " Markdown and rendered as a single page. There are no length"
        " constraints, but be reasonable.",
        max_length=body_maxlen(),
    )


class ChallengeNewsItem(DyffSchemaBaseModel):
    """A news item to display in the challenge news feed."""

    id: str = pydantic.Field(description="Unique ID of the news item.")
    title: str = pydantic.Field(
        description='A short plain string suitable as a title or "headline".',
        max_length=title_maxlen(),
    )
    summary: str = pydantic.Field(
        description="A brief summary, suitable for display in small UI elements.",
        max_length=summary_maxlen(),
    )
    postingTime: datetime = pydantic.Field(
        description="The timestamp when the news item was posted."
    )


class TeamMember(DyffSchemaBaseModel):
    """A member of a team."""

    name: str = pydantic.Field(
        description="The member's full name as it will be displayed in the UI."
        " Include all desired titles and honorifics.",
        max_length=title_maxlen(),
    )
    isCorrespondingMember: bool = pydantic.Field(
        description="Indicates that this member will receive and respond to"
        " correspondence pertaining to the team's participation in the challenge."
        " At least one member must be a corresponding member."
    )
    email: Optional[pydantic.EmailStr] = pydantic.Field(
        default=None, description="The member's email address."
    )
    orcid: Optional[str] = pydantic.Field(
        default=None, description="The member's ORCID."
    )
    url: Optional[pydantic.HttpUrl] = pydantic.Field(
        default=None,
        description="The URL of the member's personal Web page or similar.",
    )
    note: Optional[str] = pydantic.Field(
        default=None,
        description="A brief note giving additional information about the member.",
        max_length=summary_maxlen(),
    )
    affiliations: Optional[list[str]] = pydantic.Field(
        default=None,
        description="The member's affiliations, specified as keys in the"
        " .affiliations dict in the corresonding Team object.",
    )


class GoogleI18nMailingAddress(DyffSchemaBaseModel):
    """An international mailing address, in the schema used by Google's main challenge page
    i18n address metadata repository
    (https://chromium-i18n.appspot.com/ssl-address) and as interpreted by the
    Python ``google-i18n-address`` package.

    The field names depart from our camelCase convention to match the
    existing google-i18n-address format. We also use the empty string rather
    than
    """

    street_address: str = pydantic.Field(
        description="The (possibly multiline) street address.",
    )
    country_code: str = pydantic.Field(
        description="Two-letter ISO 3166-1 country code.",
    )
    city: Optional[str] = pydantic.Field(
        default=None,
        description="A city or town name.",
    )
    country_area: Optional[str] = pydantic.Field(
        default=None,
        description="A designation of a region, province, or state.",
    )
    postal_code: Optional[str] = pydantic.Field(
        default=None,
        description="A postal code or zip code.",
    )
    sorting_code: Optional[str] = pydantic.Field(
        default=None,
        description="A sorting code.",
    )
    name: Optional[str] = pydantic.Field(
        default=None,
        description="A person's name.",
    )
    company_name: Optional[str] = pydantic.Field(
        default=None,
        description="A name of a company or organization.",
    )

    formatted: str = pydantic.Field(
        default="",
        description="The address formatted as a multi-line string (auto-generated).",
    )

    @pydantic.model_validator(mode="after")
    def normalize_address(self):
        """Normalizes the address and populates .formatted."""
        unnormalized = self.model_dump()
        normalized = i18naddress.normalize_address(unnormalized)
        for k, v in normalized.items():
            if v != "":
                setattr(self, k, v)
        self.formatted = i18naddress.format_address(normalized, latin=True)
        return self


class TeamAffiliation(DyffSchemaBaseModel):
    """An organization with which one or more team members are affiliated, such as a
    university or company."""

    name: str = pydantic.Field(
        description="The name of the organization as it will be displayed in the UI.",
        max_length=title_maxlen(),
    )
    department: Optional[str] = pydantic.Field(
        default=None,
        description="A department within the organization.",
        max_length=title_maxlen(),
    )
    group: Optional[str] = pydantic.Field(
        default=None,
        description="A group within the organization or department.",
        max_length=title_maxlen(),
    )

    address: Optional[GoogleI18nMailingAddress] = pydantic.Field(
        default=None,
        description="The mailing address of the organization.",
    )

    url: Optional[pydantic.HttpUrl] = pydantic.Field(
        default=None, description="The organization's Web page or similar."
    )
    note: Optional[str] = pydantic.Field(
        default=None,
        description="A brief note giving additional information about the organization.",
        max_length=summary_maxlen(),
    )


class TeamBase(DyffSchemaBaseModel):
    """The members and affiliations of a team."""

    members: dict[str, TeamMember] = pydantic.Field(
        description="The members of this team"
    )
    affiliations: dict[str, TeamAffiliation] = pydantic.Field(
        description="The affiliations of the team. Team members state their"
        " affiliations by referencing these entries by their keys."
    )


class Team(DyffEntity, TeamBase):
    """The members and affiliations of a team that has entered a challenge."""

    kind: Literal["Team"] = Entities.Team.value

    challenge: str = pydantic.Field(
        description="ID of the Challenge that this Team is participating in"
    )

    def _dependencies(self) -> list[str]:
        return []

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class ChallengeTaskExecutionEnvironment(DyffSchemaBaseModel):
    """Description of an execution environment that is available to run challenge
    entries.

    The specified computational resources are maximums; entries are free to request and
    use fewer resources.
    """

    cpu: Quantity = pydantic.Field(
        description="Number of available CPUs. Uses k8s Quantity notation."
    )
    memory: Quantity = pydantic.Field(
        description="Available memory. Uses k8s Quantity notation."
    )
    accelerators: dict[str, int] = pydantic.Field(
        default_factory=dict,
        description="Available accelerators; the keys are accelerator types"
        " and the values are the available count.",
    )


class ChallengeTaskExecutionEnvironmentChoices(DyffSchemaBaseModel):
    """The execution environment(s) available to run challenge entries.

    For an InferenceService to be a valid submission for a Challenge, there must be at
    least one execution environment defined for the challenge such that all of the
    resource requests of the service are less than or equal to the corresponding limits
    defined in the execution environment.
    """

    choices: dict[str, ChallengeTaskExecutionEnvironment] = pydantic.Field(
        description="The choices of execution environment.",
        min_length=1,
    )


class ChallengeTaskSchedule(DyffSchemaBaseModel):
    """The schedule of a challenge task."""

    openingTime: Optional[datetime] = pydantic.Field(
        default=None, description="The announced opening time for task submissions."
    )
    closingTime: Optional[datetime] = pydantic.Field(
        default=None, description="The announced closing time for task submissions."
    )
    submissionCycleDuration: timedelta = pydantic.Field(
        default=timedelta(days=1),
        description="The duration of a submission cycle."
        " Teams are limited to a maximum number of submissions per cycle.",
    )
    submissionCycleEpoch: datetime = pydantic.Field(
        default=datetime.fromtimestamp(0, timezone.utc),
        description="The epoch of a submission cycle."
        " For example, any given cycle lasts from"
        " [epoch + N*duration, epoch + (N+1)*duration)."
        " Teams are limited to a maximum number of submissions per cycle.",
    )
    submissionLimitPerCycle: int = pydantic.Field(
        default=1,
        ge=1,
        description="Teams are limited to this many submissions per cycle.",
    )

    @pydantic.model_validator(mode="after")
    def _validate_times(self):
        """Basic temporal sanity checks."""
        if (
            self.openingTime
            and self.closingTime
            and self.closingTime <= self.openingTime
        ):
            raise ValueError("closingTime must be after openingTime")
        if self.submissionCycleDuration <= timedelta(0):
            raise ValueError("submissionCycleDuration must be positive")
        return self


class ChallengeTaskRules(DyffSchemaBaseModel):
    """The rules of the challenge."""

    executionEnvironment: ChallengeTaskExecutionEnvironmentChoices = pydantic.Field(
        description="The available choices for the execution environment."
    )
    schedule: ChallengeTaskSchedule = pydantic.Field(
        default_factory=ChallengeTaskSchedule, description="The challenge schedule."
    )


class ChallengeTaskContent(DyffSchemaBaseModel):
    """The content of a ChallengeTask UI view."."""

    page: ChallengeContentPage = pydantic.Field(
        default_factory=ChallengeContentPage,
        description="The content of the challenge task Web page.",
    )


class SubmissionStructure(DyffSchemaBaseModel):
    submissionKind: EntityKindLiteral = pydantic.Field(
        default=Entities.InferenceService.value,
        description="The kind of entity that you can submit to this task.",
    )
    pipelineKeyword: str = pydantic.Field(
        default="submission",
        description="The keyword parameter where the submitted entity ID"
        " should be passed to the assessment Pipeline.",
    )


class ChallengeTaskBase(DyffSchemaBaseModel):
    """The part of the ChallengeTask spec that is not system-populated."""

    challenge: str = pydantic.Field(
        description="The ID of the Challenge of which this task is a member."
    )
    name: str = pydantic.Field(
        description="Unique name for the task in the context of the challenge."
        " This may appear in URLs and must follow naming restrictions.",
        max_length=title_maxlen(),
        pattern=r"[a-z0-9-]*",
        min_length=1,
    )
    assessment: str = pydantic.Field(
        description="ID of the Pipeline used to assess the submission."
    )
    submissionStructure: SubmissionStructure = pydantic.Field(
        default_factory=SubmissionStructure,
        description="How to run the assessment pipeline on a new submission.",
    )
    rules: ChallengeTaskRules = pydantic.Field(description="The rules for submissions.")
    content: ChallengeTaskContent = pydantic.Field(
        default_factory=ChallengeTaskContent,
        description="Content of the task view in the Dyff App.",
    )


class ChallengeTask(Status, ChallengeTaskBase, DyffModelWithID):
    """A task that is part of a challenge.

    Teams make submissions to individual tasks, rather than the overall challenge. A
    task combines an assessment pipeline that actually implements the computations along
    with rules for submissions and descriptive content for the Web app.
    """

    creationTime: datetime = pydantic.Field(
        description="Resource creation time (assigned by system)"
    )

    lastTransitionTime: Optional[datetime] = pydantic.Field(
        default=None, description="Time of last (status, reason) change."
    )


class ChallengeContent(DyffSchemaBaseModel):
    """The content of a Challenge UI view."."""

    page: ChallengeContentPage = pydantic.Field(
        default_factory=ChallengeContentPage,
        description="The content of the challenge Web page.",
    )
    news: dict[str, ChallengeNewsItem] = pydantic.Field(
        default_factory=dict,
        description="News items to display in the challenge news feed.",
    )


class Challenge(DyffEntity):
    """A Challenge is a collection of assessments on which participating teams compete
    to achieve the best performance."""

    kind: Literal["Challenge"] = Entities.Challenge.value

    content: ChallengeContent = pydantic.Field(
        description="Content of the challenge view in the Dyff App."
    )

    tasks: dict[str, ChallengeTask] = pydantic.Field(
        default_factory=dict, description="The assessments that comprise the challenge."
    )

    def _dependencies(self) -> list[str]:
        return []

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class SubmissionBase(DyffSchemaBaseModel):
    team: str = pydantic.Field(description="The ID of the team making the submission.")
    submission: EntityIdentifier = pydantic.Field(
        description="The resource being submitted for assessment."
    )


class Submission(DyffEntity, SubmissionBase):
    """A submission of an inference system to a challenge by a team.

    All of the constituent resources must already exist. Creating a Submission simply
    indicates that the participating team wishes to submit the inference service as an
    official entry. Most challenges will limit the number of submissions that can be
    made in a given time interval.
    """

    kind: Literal["Submission"] = Entities.Submission.value

    challenge: str = pydantic.Field(
        description="The ID of the challenge being submitted to."
    )
    task: str = pydantic.Field(
        description="The key of the task within the challenge being submitted to."
    )
    pipelineRun: str = pydantic.Field(
        description="The ID of the PipelineRun for this submission."
    )

    def _dependencies(self) -> list[str]:
        return []

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


# ---------------------------------------------------------------------------
# Pipelines


class PipelineEvaluationRequest(EvaluationRequestBase):
    kind: Literal["PipelineEvaluationRequest"] = "PipelineEvaluationRequest"

    def dependencies(self) -> list[str]:
        if self.inferenceSession is None:
            raise AssertionError()
        return [self.dataset, self.inferenceSession.inferenceService]

    @pydantic.model_validator(mode="after")
    def check_session_not_reference(self):
        if self.inferenceSession is None or self.inferenceSessionReference is not None:
            raise ValueError(
                "evaluations in pipelines must set inferenceSession, not inferenceSessionReference"
            )
        return self


class PipelineMeasurementRequest(AnalysisRequestBase):
    kind: Literal["PipelineMeasurementRequest"] = "PipelineMeasurementRequest"

    def dependencies(self) -> list[str]:
        return [self.method] + [x.entity for x in self.inputs]


class PipelineSafetyCaseRequest(AnalysisRequestBase):
    kind: Literal["PipelineSafetyCaseRequest"] = "PipelineSafetyCaseRequest"

    def dependencies(self) -> list[str]:
        return [self.method] + [x.entity for x in self.inputs]


PipelineNodeRequest = Union[
    PipelineEvaluationRequest,
    PipelineMeasurementRequest,
    PipelineSafetyCaseRequest,
]


class PipelineNode(DyffSchemaBaseModel):
    """A node in the graph that defines the pipeline.

    Each node contains a Dyff API request that might depend on the outcome of other
    requests in the pipeline graph. When the pipeline runs, the requests are executed in
    an order that respects these dependencies.
    """

    name: str = pydantic.Field(
        description="The name of the node. Must be unique in the context of the pipeline."
    )

    request: PipelineNodeRequest = pydantic.Field(
        description="The request template that will be executed when this node"
        ' executes. You can use the syntax "$(node_name)" in request fields'
        " that reference another entity to indicate that the request depends"
        " on another node in the pipeline. The placeholder will be substituted"
        " with the ID of the created entity once it is known. Dyff infers the"
        " dependency graph structure from these placeholders.",
    )

    # The .kind field is dropped when we serialize nodes as part of a
    # PipelineCreateRequest because of the default exclude_unset=True
    # behavior for requests, so we add it back.
    @pydantic.field_serializer("request")
    def _serialize_request(self, request: PipelineNodeRequest, _info):
        data = request.model_dump(mode=_info.mode)
        data["kind"] = request.kind
        return data


class PipelineParameter(DyffSchemaBaseModel):
    """Declares a parameter that can be passed to the pipeline to customize its
    behavior.

    By default, the argument will be substituted for the placeholder value
    ``$(keyword)``, where ``keyword`` is the ``.keyword`` property of the
    parameter. In this case, the value of the argument must be a string.

    If ``.destination`` is specified, the argument will instead overwrite
    the value at the specified JSON path.
    """

    keyword: str = pydantic.Field(description="The keyword of the parameter.")
    destination: Optional[str] = pydantic.Field(
        default=None,
        description="The field in a pipeline node to substitute with the"
        " parameter value. Should be a string like 'node_name.field1.field2'.",
    )
    description: Optional[str] = pydantic.Field(
        default=None,
        description="A description of the parameter.",
        max_length=summary_maxlen(),
    )


class PipelineBase(DyffSchemaBaseModel):
    name: str = pydantic.Field(description="The name of the Pipeline.")
    nodes: dict[str, PipelineNode] = pydantic.Field(
        description="The nodes in the pipeline graph.",
        min_length=1,
    )
    parameters: dict[str, PipelineParameter] = pydantic.Field(
        default_factory=dict,
        description="Input parameters used to customize the pipeline.",
    )

    @pydantic.field_validator("nodes", mode="after")
    def validate_node_names_match(cls, nodes: dict[str, PipelineNode]):
        for k, v in nodes.items():
            if k != v.name:
                raise ValueError(f"nodes[{k}]: dict key must match value.name")
        return nodes

    @pydantic.field_validator("parameters", mode="after")
    def validate_parameter_keywords_match(
        cls, parameters: dict[str, PipelineParameter]
    ):
        for k, v in parameters.items():
            if k != v.keyword:
                raise ValueError(f"parameters[{k}]: dict key must match value.keyword")
        return parameters


class Pipeline(DyffEntity, PipelineBase):
    """A set of Dyff workflows that can be executed as a group.

    The pipeline is a directed acyclic graph representing data dependencies
    between workflows. For example, a simple pipeline might run an Evaluation
    and then create a SafetyCase from the evaluation output. This pipeline would
    have a graph structure like ``evaluation -> safetycase``.

    Each node in the pipeline contains the specification of a Dyff API request.
    The request specifications may contain placeholders that reference other
    nodes in the pipeline graph. When the pipeline is run, the nodes execute
    in an order that respects their dependencies, and the placeholders are
    replaced with concrete values once they are known.
    """

    kind: Literal["Pipeline"] = Entities.Pipeline.value

    def _dependencies(self) -> list[str]:
        return []

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class PipelineRunBase(DyffSchemaBaseModel):
    """A pipeline run is an execution of a pipeline."""

    pipeline: str = pydantic.Field(description="The ID of the pipeline that was run.")
    arguments: dict[str, pydantic.JsonValue] = pydantic.Field(
        default_factory=dict,
        description="The arguments to pass to the pipeline.",
    )


class PipelineRun(DyffEntity, PipelineRunBase):
    kind: Literal["PipelineRun"] = Entities.PipelineRun.value

    workflows: dict[str, EntityIdentifier] = pydantic.Field(
        description="The concrete IDs of the workflows that were created as a"
        " result of running the pipeline."
    )

    def _dependencies(self) -> list[str]:
        return [self.pipeline]

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


class PipelineRunStatus(Status):
    nodes: dict[str, Status] = pydantic.Field(
        default_factory=dict, description="The status of each pipeline node."
    )


# ---------------------------------------------------------------------------
# Status enumerations


class _JobStatus(NamedTuple):
    """The set of basic ``status`` values that are applicable to all "job" entities
    (entities that involve computation tasks)."""

    complete: str = "Complete"
    failed: str = "Failed"


JobStatus = _JobStatus()


class _ResourceStatus(NamedTuple):
    """The set of basic ``status`` values that are applicable to all "resource"
    entities."""

    ready: str = "Ready"
    error: str = "Error"


ResourceStatus = _ResourceStatus()


class _EntityStatus(NamedTuple):
    """The set of basic ``status`` values that are applicable to most entity types."""

    created: str = "Created"
    schedulable: str = "Schedulable"
    admitted: str = "Admitted"
    terminated: str = "Terminated"
    deleted: str = "Deleted"
    ready: str = ResourceStatus.ready
    complete: str = JobStatus.complete
    error: str = ResourceStatus.error
    failed: str = JobStatus.failed
    denied: str = "Denied"
    approved: str = "Approved"


EntityStatus = _EntityStatus()


class _EntityStatusReason(NamedTuple):
    """The set of basic ``reason`` values that are applicable to most entity types."""

    quota_limit: str = "QuotaLimit"
    unsatisfied_dependency: str = "UnsatisfiedDependency"
    failed_dependency: str = "FailedDependency"
    terminate_command: str = "TerminateCommand"
    delete_command: str = "DeleteCommand"
    expired: str = "Expired"
    interrupted: str = "Interrupted"


EntityStatusReason = _EntityStatusReason()


class _AuditStatus(NamedTuple):
    """The set of ``status`` values that are applicable to ``Audit`` entities."""

    created: str = EntityStatus.created
    admitted: str = EntityStatus.admitted
    complete: str = EntityStatus.complete
    failed: str = EntityStatus.failed


AuditStatus = _AuditStatus()


class _DataSources(NamedTuple):
    huggingface: str = "huggingface"
    upload: str = "upload"
    zenodo: str = "zenodo"


DataSources = _DataSources()


class _DataSourceStatus(NamedTuple):
    """The set of ``status`` values that are applicable to ``DataSource`` entities."""

    created: str = EntityStatus.created
    admitted: str = EntityStatus.admitted
    ready: str = EntityStatus.ready
    error: str = EntityStatus.error


DataSourceStatus = _DataSourceStatus()


class _DataSourceStatusReason(NamedTuple):
    """The set of ``reason`` values that are applicable to ``DataSource`` entities."""

    quota_limit: str = EntityStatusReason.quota_limit
    fetch_failed: str = "FetchFailed"
    upload_failed: str = "UploadFailed"


DataSourceStatusReason = _DataSourceStatusReason()


class _DatasetStatus(NamedTuple):
    """The set of ``status`` values that are applicable to ``Dataset`` entities."""

    created: str = EntityStatus.created
    admitted: str = EntityStatus.admitted
    ready: str = EntityStatus.ready
    error: str = EntityStatus.error


DatasetStatus = _DatasetStatus()


class _DatasetStatusReason(NamedTuple):
    """The set of ``reason`` values that are applicable to ``Dataset`` entities."""

    quota_limit: str = EntityStatusReason.quota_limit
    data_source_missing: str = "DataSourceMissing"
    ingest_failed: str = "IngestFailed"
    waiting_for_data_source: str = "WaitingForDataSource"


DatasetStatusReason = _DatasetStatusReason()


class _EvaluationStatus(NamedTuple):
    """The set of ``status`` values that are applicable to ``Evaluation`` entities."""

    created: str = EntityStatus.created
    admitted: str = EntityStatus.admitted
    complete: str = EntityStatus.complete
    failed: str = EntityStatus.failed


EvaluationStatus = _EvaluationStatus()


class _EvaluationStatusReason(NamedTuple):
    """The set of ``reason`` values that are applicable to ``Evaluation`` entities."""

    quota_limit: str = EntityStatusReason.quota_limit
    incomplete: str = "Incomplete"
    unverified: str = "Unverified"
    restarted: str = "Restarted"


EvaluationStatusReason = _EvaluationStatusReason()


class _ModelStatus(NamedTuple):
    """The set of ``status`` values that are applicable to ``Model`` entities."""

    created: str = EntityStatus.created
    admitted: str = EntityStatus.admitted
    ready: str = EntityStatus.ready
    error: str = EntityStatus.error


ModelStatus = _ModelStatus()


class _ModelStatusReason(NamedTuple):
    """The set of ``reason`` values that are applicable to ``Model`` entities."""

    quota_limit: str = EntityStatusReason.quota_limit
    fetch_failed: str = "FetchFailed"


ModelStatusReason = _ModelStatusReason()


class _InferenceServiceStatus(NamedTuple):
    """The set of ``status`` values that are applicable to ``InferenceService``
    entities."""

    created: str = EntityStatus.created
    admitted: str = EntityStatus.admitted
    ready: str = EntityStatus.ready
    error: str = EntityStatus.error


InferenceServiceStatus = _InferenceServiceStatus()


class _InferenceServiceStatusReason(NamedTuple):
    """The set of ``reason`` values that are applicable to ``InferenceService``
    entities."""

    quota_limit: str = EntityStatusReason.quota_limit
    build_failed: str = "BuildFailed"
    no_such_model: str = "NoSuchModel"
    waiting_for_model: str = "WaitingForModel"


InferenceServiceStatusReason = _InferenceServiceStatusReason()


class _ReportStatus(NamedTuple):
    """The set of ``status`` values that are applicable to ``Report`` entities."""

    created: str = EntityStatus.created
    admitted: str = EntityStatus.admitted
    complete: str = EntityStatus.complete
    failed: str = EntityStatus.failed


ReportStatus = _ReportStatus()


class _ReportStatusReason(NamedTuple):
    """The set of ``reason`` values that are applicable to ``Report`` entities."""

    quota_limit: str = EntityStatusReason.quota_limit
    no_such_evaluation: str = "NoSuchEvaluation"
    waiting_for_evaluation: str = "WaitingForEvaluation"


ReportStatusReason = _ReportStatusReason()


def is_status_terminal(status: str) -> bool:
    return status in [
        EntityStatus.approved,
        EntityStatus.complete,
        EntityStatus.deleted,
        EntityStatus.denied,
        EntityStatus.error,
        EntityStatus.failed,
        EntityStatus.ready,
        EntityStatus.terminated,
    ]


def is_status_failure(status: str) -> bool:
    return status in [EntityStatus.error, EntityStatus.failed, EntityStatus.denied]


def is_status_success(status: str) -> bool:
    return status in [EntityStatus.complete, EntityStatus.ready, EntityStatus.approved]


# A Union type containing all Dyff top-level schema types, except the ones that
# should not have Revisions generated for them when they change
_DyffEntityTypeRevisable = Union[
    Audit,
    AuditProcedure,
    Challenge,
    DataSource,
    Dataset,
    Evaluation,
    Family,
    Hazard,
    InferenceService,
    InferenceSession,
    Measurement,
    Method,
    Model,
    Module,
    OCIArtifact,
    Pipeline,
    PipelineRun,
    Report,
    SafetyCase,
    Submission,
    Team,
    UseCase,
]


class RevisionData(DyffSchemaBaseModel):
    format: Literal["Snapshot", "JsonMergePatch"]
    snapshot: Optional[_DyffEntityTypeRevisable] = pydantic.Field(
        default=None, description="A full snapshot of the entity."
    )
    jsonMergePatch: Optional[str] = pydantic.Field(
        default=None,
        description="A JsonMergePatch, serialized as a string, that will"
        " transform the *current* revision into the *previous* revision.",
    )


# Note: This class is defined here because OpenAPI generation doesn't work
# with the Python < 3.10 "ForwardDeclaration" syntax. You get an error like:
#
# Traceback (most recent call last):
#   File "/home/jessehostetler/dsri/code/dyff/dyff-api/./scripts/generate-openapi-definitions.py", line 15, in <module>
#     get_openapi(
#   File "/home/jessehostetler/dsri/code/dyff/venv/lib/python3.9/site-packages/fastapi/openapi/utils.py", line 422, in get_openapi
#     definitions = get_model_definitions(
#   File "/home/jessehostetler/dsri/code/dyff/venv/lib/python3.9/site-packages/fastapi/utils.py", line 60, in get_model_definitions
#     m_schema, m_definitions, m_nested_models = model_process_schema(
#   File "pydantic/schema.py", line 581, in pydantic.schema.model_process_schema
#   File "pydantic/schema.py", line 622, in pydantic.schema.model_type_schema
#   File "pydantic/schema.py", line 255, in pydantic.schema.field_schema
#   File "pydantic/schema.py", line 527, in pydantic.schema.field_type_schema
#   File "pydantic/schema.py", line 926, in pydantic.schema.field_singleton_schema
#   File "/home/jessehostetler/.asdf/installs/python/3.9.18/lib/python3.9/abc.py", line 123, in __subclasscheck__
#     return _abc_subclasscheck(cls, subclass)
# TypeError: issubclass() arg 1 must be a class
class Revision(DyffEntity, RevisionMetadata):
    kind: Literal["Revision"] = "Revision"

    revisionOf: str = pydantic.Field(
        description="The ID of the entity that this is a revision of"
    )

    data: RevisionData = pydantic.Field(
        description="The associated entity revision data",
    )

    def _dependencies(self) -> list[str]:
        return []

    def resource_allocation(self) -> Optional[ResourceAllocation]:
        return None


# A Union type containing all Dyff top-level schema types
DyffEntityType = Union[_DyffEntityTypeRevisable, History, Revision]


_ENTITY_CLASS: dict[Entities, type[DyffEntityType]] = {
    Entities.Artifact: OCIArtifact,
    Entities.Audit: Audit,
    Entities.AuditProcedure: AuditProcedure,
    Entities.Challenge: Challenge,
    Entities.Dataset: Dataset,
    Entities.DataSource: DataSource,
    Entities.Evaluation: Evaluation,
    Entities.Family: Family,
    Entities.Hazard: Hazard,
    Entities.History: History,
    Entities.InferenceService: InferenceService,
    Entities.InferenceSession: InferenceSession,
    Entities.Measurement: Measurement,
    Entities.Method: Method,
    Entities.Model: Model,
    Entities.Module: Module,
    Entities.Pipeline: Pipeline,
    Entities.PipelineRun: PipelineRun,
    Entities.Report: Report,
    Entities.Revision: Revision,
    Entities.SafetyCase: SafetyCase,
    Entities.Submission: Submission,
    Entities.Team: Team,
    Entities.UseCase: UseCase,
}


def entity_class(kind: Entities) -> type[DyffEntityType]:
    return _ENTITY_CLASS[kind]


# A TypeVar that matches any Dyff top-level schema type
DyffEntityT = TypeVar(
    "DyffEntityT",
    Audit,
    AuditProcedure,
    Challenge,
    DataSource,
    Dataset,
    Evaluation,
    Family,
    Hazard,
    History,
    InferenceService,
    InferenceSession,
    Measurement,
    Method,
    Model,
    Module,
    OCIArtifact,
    Pipeline,
    PipelineRun,
    Report,
    Revision,
    SafetyCase,
    Submission,
    Team,
    UseCase,
)


__all__ = [
    "SYSTEM_ATTRIBUTES",
    "Accelerator",
    "AcceleratorGPU",
    "AccessGrant",
    "Account",
    "Analysis",
    "AnalysisArgument",
    "AnalysisBase",
    "AnalysisData",
    "AnalysisInput",
    "AnalysisOutputQueryFields",
    "AnalysisRequestBase",
    "AnalysisScope",
    "Annotation",
    "APIFunctions",
    "APIKey",
    "ArchiveFormat",
    "Artifact",
    "ArtifactURL",
    "Audit",
    "AuditProcedure",
    "AuditRequirement",
    "Challenge",
    "ChallengeContent",
    "ChallengeContentPage",
    "ChallengeTask",
    "ChallengeTaskBase",
    "ChallengeTaskContent",
    "ChallengeTaskExecutionEnvironment",
    "ChallengeTaskExecutionEnvironmentChoices",
    "ChallengeTaskRules",
    "ChallengeTaskSchedule",
    "Concern",
    "ConcernBase",
    "Container",
    "ContainerImageSource",
    "Curve",
    "CurveData",
    "CurveSpec",
    "DataSchema",
    "Dataset",
    "DatasetBase",
    "DatasetFilter",
    "DataSource",
    "DataSources",
    "DataView",
    "Digest",
    "Documentation",
    "DocumentationBase",
    "Documented",
    "DyffDataSchema",
    "DyffEntity",
    "DyffEntityMetadata",
    "DyffEntityT",
    "DyffEntityType",
    "DyffModelWithID",
    "DyffSchemaBaseModel",
    "Entities",
    "EntityID",
    "EntityIdentifier",
    "EntityIDField",
    "EntityIDMarker",
    "EntityKindLiteral",
    "Evaluation",
    "EvaluationBase",
    "EvaluationClientConfiguration",
    "EvaluationRequestBase",
    "ExtractorStep",
    "Family",
    "FamilyBase",
    "FamilyMember",
    "FamilyMemberBase",
    "FamilyMemberKind",
    "FamilyMembers",
    "File",
    "FileStorageURL",
    "ForeignInferenceService",
    "ForeignMethod",
    "ForeignModel",
    "ForeignRevision",
    "Frameworks",
    "Hazard",
    "History",
    "Identity",
    "InferenceInterface",
    "InferenceService",
    "InferenceServiceBase",
    "InferenceServiceBuilder",
    "InferenceServiceRunner",
    "InferenceServiceRunnerKind",
    "InferenceServiceSources",
    "InferenceServiceSpec",
    "InferenceSession",
    "InferenceSessionAndToken",
    "InferenceSessionBase",
    "InferenceSessionReference",
    "InferenceSessionSpec",
    "Label",
    "LabelKey",
    "LabelKeyType",
    "LabelValue",
    "LabelValueType",
    "Labeled",
    "Measurement",
    "MeasurementLevel",
    "MeasurementSpec",
    "Method",
    "MethodBase",
    "MethodImplementation",
    "MethodImplementationJupyterNotebook",
    "MethodImplementationKind",
    "MethodImplementationPythonFunction",
    "MethodImplementationPythonRubric",
    "MethodInput",
    "MethodInputKind",
    "MethodOutput",
    "MethodOutputKind",
    "MethodParameter",
    "MethodScope",
    "Metrics",
    "MetricValue",
    "Model",
    "ModelArtifact",
    "ModelArtifactHuggingFaceCache",
    "ModelArtifactKind",
    "ModelBase",
    "ModelStorageMedium",
    "ModelResources",
    "ModelSource",
    "ModelSourceGitLFS",
    "ModelSourceHuggingFaceHub",
    "ModelSourceKinds",
    "ModelSourceOpenLLM",
    "ModelSpec",
    "ModelStorage",
    "Module",
    "ModuleBase",
    "OCIArtifact",
    "Pipeline",
    "PipelineBase",
    "PipelineEvaluationRequest",
    "PipelineMeasurementRequest",
    "PipelineNode",
    "PipelineParameter",
    "PipelineRun",
    "PipelineRunBase",
    "PipelineRunStatus",
    "PipelineSafetyCaseRequest",
    "QueryableDyffEntity",
    "Report",
    "ReportBase",
    "Resources",
    "ResourceRequirements",
    "Revision",
    "RevisionData",
    "RevisionMetadata",
    "Role",
    "SafetyCase",
    "SafetyCaseSpec",
    "SchemaAdapter",
    "Score",
    "ScoreData",
    "ScoreSpec",
    "ScoreMetadata",
    "ScoreMetadataRefs",
    "SecurityContext",
    "Status",
    "StorageSignedURL",
    "Submission",
    "SubmissionBase",
    "SubmissionStructure",
    "TagName",
    "TagNameType",
    "TaskSchema",
    "Team",
    "TeamBase",
    "TeamMember",
    "TeamAffiliation",
    "UseCase",
    "Volume",
    "VolumeMount",
    "VolumeMountData",
    "VolumeMountKind",
    "VolumeMountScratch",
    "entity_class",
    "JobStatus",
    "EntityStatus",
    "EntityStatusReason",
    "AuditStatus",
    "DataSourceStatus",
    "DatasetStatus",
    "DatasetStatusReason",
    "EvaluationStatus",
    "EvaluationStatusReason",
    "InferenceServiceStatus",
    "InferenceServiceStatusReason",
    "ModelStatus",
    "ModelStatusReason",
    "ReportStatus",
    "ReportStatusReason",
    "body_maxlen",
    "identifier_regex",
    "identifier_maxlen",
    "is_status_terminal",
    "is_status_failure",
    "is_status_success",
    "summary_maxlen",
    "title_maxlen",
]
