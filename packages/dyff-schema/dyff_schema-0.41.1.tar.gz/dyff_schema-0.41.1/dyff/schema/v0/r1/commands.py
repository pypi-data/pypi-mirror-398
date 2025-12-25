# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0
"""The command schemas describe the API for the command model.

These are used internally by the platform and users typically won't encounter them.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal, Optional, Union

import pydantic
from pydantic import StringConstraints, field_serializer
from typing_extensions import Annotated

from .base import DyffSchemaBaseModel, JsonMergePatchSemantics
from .platform import (
    ChallengeNewsItem,
    ChallengeTask,
    ChallengeTaskExecutionEnvironment,
    ChallengeTaskSchedule,
    DyffEntityType,
    EntityIdentifier,
    FamilyMember,
    FamilyMembers,
    LabelKeyType,
    LabelValueType,
    SchemaVersion,
    Status,
    TagNameType,
    Team,
    TeamAffiliation,
    TeamMember,
    body_maxlen,
    summary_maxlen,
    title_maxlen,
)


class FamilyIdentifier(EntityIdentifier):
    """Identifies a single Family entity."""

    kind: Literal["Family"] = "Family"


class Command(SchemaVersion, DyffSchemaBaseModel):
    """Base class for Command messages.

    Commands define the API of the "command model" in our CQRS architecture.
    """

    command: Literal[
        "CreateChallengeTask",
        "CreateChallengeTeam",
        "CreateEntity",
        "EditChallengeContent",
        "EditChallengeTaskRules",
        "EditEntityDocumentation",
        "EditEntityLabels",
        "EditFamilyMembers",
        "EditTeam",
        "ForgetEntity",
        "RestoreEntity",
        "UpdateEntityStatus",
    ]


# ----------------------------------------------------------------------------


class CreateEntity(Command):
    """Create a new entity."""

    command: Literal["CreateEntity"] = "CreateEntity"

    data: DyffEntityType = pydantic.Field(
        description="The full spec of the entity to create."
    )


# ----------------------------------------------------------------------------


class CreateChallengeTaskAttributes(DyffSchemaBaseModel):
    """Attributes for the CreateChallengeTask command."""

    task: ChallengeTask = pydantic.Field(description="The task to create.")


class CreateChallengeTaskData(EntityIdentifier):
    """Payload data for the CreateChallengeTask command."""

    attributes: CreateChallengeTaskAttributes = pydantic.Field(
        description="The command attributes"
    )


class CreateChallengeTask(Command):
    """Create a new challenge task within an existing challenge."""

    command: Literal["CreateChallengeTask"] = "CreateChallengeTask"

    data: CreateChallengeTaskData = pydantic.Field(description="The command data.")


# ----------------------------------------------------------------------------


class CreateChallengeTeamAttributes(DyffSchemaBaseModel):
    """Attributes for the CreateChallengeTeam command."""

    team: Team = pydantic.Field(description="The team to create.")


class CreateChallengeTeamData(EntityIdentifier):
    """Payload data for the CreateChallengeTeam command."""

    attributes: CreateChallengeTeamAttributes = pydantic.Field(
        description="The command attributes"
    )


class CreateChallengeTeam(Command):
    """Create a new team participating in an existing challenge."""

    command: Literal["CreateChallengeTeam"] = "CreateChallengeTeam"

    data: CreateChallengeTeamData = pydantic.Field(description="The command data.")


# ----------------------------------------------------------------------------


class ChallengeContentPagePatch(JsonMergePatchSemantics):
    """Same properties as ChallengeContentPage.

    Fields that are not assigned explicitly remain unchanged.
    """

    title: Annotated[str, StringConstraints(max_length=title_maxlen())] = (  # type: ignore
        pydantic.Field(
            default="",
            description='A short plain string suitable as a title or "headline".',
        )
    )

    summary: Annotated[str, StringConstraints(max_length=summary_maxlen())] = (  # type: ignore
        pydantic.Field(
            default="",
            description="A brief summary, suitable for display in"
            " small UI elements.",
        )
    )

    body: Annotated[str, StringConstraints(max_length=body_maxlen())] = pydantic.Field(  # type: ignore
        default="",
        description="Long-form documentation. Interpreted as"
        " Markdown. There are no length constraints, but be reasonable.",
    )


class ChallengeContentPatch(DyffSchemaBaseModel):
    page: ChallengeContentPagePatch = pydantic.Field(
        default_factory=ChallengeContentPagePatch,
        description="Edits to make to the page portion of the content.",
    )

    news: Optional[dict[str, ChallengeNewsItem]] = pydantic.Field(
        default=None,
        description="News items to display in the challenge news feed.",
    )

    @field_serializer("page")
    def _serialize_page(self, page: ChallengeContentPagePatch, _info):
        return page.model_dump(mode=_info.mode)


class EditChallengeContentPatch(DyffSchemaBaseModel):
    content: Optional[ChallengeContentPatch] = pydantic.Field(
        default=None,
        description="Edits to make to the content of the challenge-related resource.",
    )


class EditChallengeContentAttributes(EditChallengeContentPatch):
    """Attributes for the EditChallengeContent command."""

    tasks: Optional[dict[str, EditChallengeContentPatch]] = pydantic.Field(
        default=None, description="Edits to make to the content of the challenge tasks."
    )


class EditChallengeContentData(EntityIdentifier):
    """Payload data for the EditChallengeContent command."""

    attributes: EditChallengeContentAttributes = pydantic.Field(
        description="The command attributes"
    )


class EditChallengeContent(Command):
    """Edit the page content associated with a challenge-related entity.

    Setting a documentation field to null/None deletes the corresponding value. To
    preserve the existing value, leave the field *unset*.
    """

    command: Literal["EditChallengeContent"] = "EditChallengeContent"

    data: EditChallengeContentData = pydantic.Field(description="The edit data.")


# ----------------------------------------------------------------------------


class ChallengeTaskRulesExecutionEnvironmentPatch(JsonMergePatchSemantics):
    """Same properties as ChallengeTaskExecutionEnvironmentChocies, but assigning None
    to a field is interpreted as a command to delete that field.

    Fields that are not assigned explicitly remain unchanged.
    """

    choices: dict[str, Optional[ChallengeTaskExecutionEnvironment]] = pydantic.Field(
        default_factory=dict, description="Execution environment choices."
    )


class ChallengeTaskRulesSchedulePatch(JsonMergePatchSemantics):
    """Same properties as ChallengeTaskSchedule, but assigning None to a field is
    interpreted as a command to delete that field.

    Fields that are not assigned explicitly remain unchanged.
    """

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


class ChallengeTaskRulesPatch(DyffSchemaBaseModel):
    """Edits to make to the different rules categories."""

    executionEnvironment: ChallengeTaskRulesExecutionEnvironmentPatch = pydantic.Field(
        default_factory=ChallengeTaskRulesExecutionEnvironmentPatch,
        description="Patch for the .rules.executionEnvironments field.",
    )
    schedule: ChallengeTaskRulesSchedulePatch = pydantic.Field(
        default_factory=ChallengeTaskRulesSchedulePatch,
        description="Patch for the .rules.schedule field.",
    )

    @field_serializer("executionEnvironment")
    def _serialize_executionEnvironment(
        self,
        executionEnvironment: ChallengeTaskRulesExecutionEnvironmentPatch,
        _info,
    ):
        return executionEnvironment.model_dump(mode=_info.mode)

    @field_serializer("schedule")
    def _serialize_schedule(
        self,
        schedule: ChallengeTaskRulesSchedulePatch,
        _info,
    ):
        return schedule.model_dump(mode=_info.mode)


class EditChallengeTaskRulesPatch(DyffSchemaBaseModel):
    """A Json Merge Patch for the rules of one task."""

    rules: ChallengeTaskRulesPatch = pydantic.Field(
        description="Edits to make to the task rules."
    )


class EditChallengeTaskRulesAttributes(DyffSchemaBaseModel):
    """Attributes for the EditChallengeTaskRules command."""

    tasks: dict[str, EditChallengeTaskRulesPatch] = pydantic.Field(
        description="Edits to make to the task rules."
    )


class EditChallengeTaskRulesData(EntityIdentifier):
    """Payload data for the EditChallengeTaskRules command."""

    attributes: EditChallengeTaskRulesAttributes = pydantic.Field(
        description="The command attributes"
    )


class EditChallengeTaskRules(Command):
    """Edit the rules of a challenge task.

    Setting a field to null/None deletes the corresponding value. To preserve the
    existing value, leave the field *unset*.
    """

    command: Literal["EditChallengeTaskRules"] = "EditChallengeTaskRules"

    data: EditChallengeTaskRulesData = pydantic.Field(description="The edit data.")


# ----------------------------------------------------------------------------


class EditEntityDocumentationPatch(JsonMergePatchSemantics):
    """Same properties as DocumentationBase, but assigning None to a field is
    interpreted as a command to delete that field.

    Fields that are not assigned explicitly remain unchanged.
    """

    title: Optional[Annotated[str, StringConstraints(max_length=title_maxlen())]] = (  # type: ignore
        pydantic.Field(
            default=None,
            description='A short plain string suitable as a title or "headline".'
            " Providing an explicit None value deletes the current value.",
        )
    )

    summary: Optional[Annotated[str, StringConstraints(max_length=summary_maxlen())]] = (  # type: ignore
        pydantic.Field(
            default=None,
            description="A brief summary, suitable for display in"
            " small UI elements. Providing an explicit None value deletes the"
            " current value.",
        )
    )

    fullPage: Optional[str] = pydantic.Field(
        default=None,
        description="Long-form documentation. Interpreted as"
        " Markdown. There are no length constraints, but be reasonable."
        " Providing an explicit None value deletes the current value.",
    )


class EditEntityDocumentationAttributes(DyffSchemaBaseModel):
    """Attributes for the EditEntityDocumentation command."""

    documentation: EditEntityDocumentationPatch = pydantic.Field(
        description="Edits to make to the documentation."
    )

    @field_serializer("documentation")
    def _serialize_documentation(
        self, documentation: EditEntityDocumentationPatch, _info
    ):
        return documentation.model_dump(mode=_info.mode)


class EditEntityDocumentationData(EntityIdentifier):
    """Payload data for the EditEntityDocumentation command."""

    attributes: EditEntityDocumentationAttributes = pydantic.Field(
        description="The command attributes"
    )


class EditEntityDocumentation(Command):
    """Edit the documentation associated with an entity.

    Setting a documentation field to null/None deletes the corresponding value. To
    preserve the existing value, leave the field *unset*.
    """

    command: Literal["EditEntityDocumentation"] = "EditEntityDocumentation"

    data: EditEntityDocumentationData = pydantic.Field(description="The edit data.")


# ----------------------------------------------------------------------------


class EditEntityLabelsAttributes(JsonMergePatchSemantics):
    """Attributes for the EditEntityLabels command."""

    labels: dict[LabelKeyType, Optional[LabelValueType]] = pydantic.Field(
        default_factory=dict,
        description="A set of key-value labels for the resource."
        " Existing label keys that are not provided in the edit remain unchanged."
        " Providing an explicit None value deletes the corresponding key.",
    )


class EditEntityLabelsData(EntityIdentifier):
    """Payload data for the EditEntityLabels command."""

    attributes: EditEntityLabelsAttributes = pydantic.Field(
        description="The command attributes"
    )

    @field_serializer("attributes")
    def _serialize_attributes(self, attributes: EditEntityLabelsAttributes, _info):
        return attributes.model_dump(mode=_info.mode)


class EditEntityLabels(Command):
    """Edit the labels associated with an entity.

    Setting a label field to null/None deletes the corresponding value. To preserve the
    existing value, leave the field *unset*.
    """

    command: Literal["EditEntityLabels"] = "EditEntityLabels"

    data: EditEntityLabelsData = pydantic.Field(description="The edit data.")


# ----------------------------------------------------------------------------


class EditFamilyMembersAttributes(JsonMergePatchSemantics):
    """Attributes for the EditFamilyMembers command."""

    members: dict[TagNameType, Optional[FamilyMember]] = pydantic.Field(
        description="Mapping of names to IDs of member resources.",
    )


class EditFamilyMembersData(FamilyMembers, FamilyIdentifier):
    """Payload data for the EditFamilyMembers command."""

    attributes: EditFamilyMembersAttributes = pydantic.Field(
        description="The command attributes"
    )

    @field_serializer("attributes")
    def _serialize_attributes(self, attributes: EditFamilyMembersAttributes, _info):
        return attributes.model_dump(mode=_info.mode)


class EditFamilyMembers(Command):
    """Edit the labels associated with an entity.

    Setting a tag value to null/None deletes the corresponding value. To preserve the
    existing value, leave the field *unset*.
    """

    command: Literal["EditFamilyMembers"] = "EditFamilyMembers"

    data: EditFamilyMembersData = pydantic.Field(description="The edit data.")


# ----------------------------------------------------------------------------


class EditTeamAttributes(JsonMergePatchSemantics):
    """Attributes for the EditFamilyMembers command."""

    members: dict[str, Optional[TeamMember]] = pydantic.Field(
        default_factory=dict, description="The members of this team"
    )
    affiliations: dict[str, Optional[TeamAffiliation]] = pydantic.Field(
        default_factory=dict,
        description="The affiliations of the team. Team members state their"
        " affiliations by referencing these entries by their keys.",
    )

    @field_serializer("members")
    def _serialize_members(
        self, members: dict[str, Optional[TeamMember]], _info
    ) -> dict[str, Optional[dict]]:
        """Serialize members dict, ensuring nested TeamMember objects exclude None
        values.

        None values in the dict itself are preserved (for JSON Merge Patch delete
        semantics), but None values inside TeamMember objects are excluded during
        serialization.
        """
        result: dict[str, Optional[dict]] = {}
        for key, value in members.items():
            if value is None:
                result[key] = None
            else:
                result[key] = value.model_dump(mode=_info.mode)
        return result

    @field_serializer("affiliations")
    def _serialize_affiliations(
        self, affiliations: dict[str, Optional[TeamAffiliation]], _info
    ) -> dict[str, Optional[dict]]:
        """Serialize affiliations dict, ensuring nested TeamAffiliation objects exclude
        None values.

        None values in the dict itself are preserved (for JSON Merge Patch delete
        semantics), but None values inside TeamAffiliation objects are excluded during
        serialization.
        """
        result: dict[str, Optional[dict]] = {}
        for key, value in affiliations.items():
            if value is None:
                result[key] = None
            else:
                result[key] = value.model_dump(mode=_info.mode)
        return result


class EditTeamData(EntityIdentifier):
    """Payload data for the EditFamilyMembers command."""

    attributes: EditTeamAttributes = pydantic.Field(
        description="The command attributes"
    )

    @field_serializer("attributes")
    def _serialize_attributes(self, attributes: EditTeamAttributes, _info):
        return attributes.model_dump(mode=_info.mode)


class EditTeam(Command):
    command: Literal["EditTeam"] = "EditTeam"

    data: EditTeamData = pydantic.Field(description="The edit data.")


# ----------------------------------------------------------------------------


class ForgetEntity(Command):
    """Forget (permanently delete) an entity."""

    command: Literal["ForgetEntity"] = "ForgetEntity"

    data: EntityIdentifier = pydantic.Field(description="The entity to forget.")


# ----------------------------------------------------------------------------


class RestoreEntityAttributes(DyffSchemaBaseModel):
    entity: DyffEntityType = pydantic.Field(
        description="The full spec of the entity to restore."
    )

    ifRevisionMatch: Optional[str] = pydantic.Field(
        default=None,
        description="Do not change the entity if its revision does not match"
        " the given revision.",
    )

    ifRevisionUndefined: Optional[bool] = pydantic.Field(
        default=None,
        description="Allow changing entities that have no revision."
        " By default, entities with no revision will be changed if and only if"
        " no other matching criteria are specified."
        " This should be the case only for legacy data.",
    )


class RestoreEntityData(EntityIdentifier):
    attributes: RestoreEntityAttributes = pydantic.Field(
        description="The command attributes"
    )


class RestoreEntity(Command):
    """Restore an entity to a given state."""

    command: Literal["RestoreEntity"] = "RestoreEntity"

    data: RestoreEntityData = pydantic.Field(description="The command data.")


# ----------------------------------------------------------------------------


class UpdateEntityStatusAttributes(JsonMergePatchSemantics):
    """Attributes for the UpdateEntityStatus command."""

    status: str = pydantic.Field(description=Status.model_fields["status"].description)

    reason: Optional[str] = pydantic.Field(
        description=Status.model_fields["reason"].description
    )


class UpdateEntityStatusData(EntityIdentifier):
    """Payload data for the UpdateEntityStatus command."""

    attributes: UpdateEntityStatusAttributes = pydantic.Field(
        description="The command attributes"
    )

    @field_serializer("attributes")
    def _serialize_attributes(self, attributes: UpdateEntityStatusAttributes, _info):
        return attributes.model_dump(mode=_info.mode)


class UpdateEntityStatus(Command):
    """Update the status fields of an entity."""

    command: Literal["UpdateEntityStatus"] = "UpdateEntityStatus"

    data: UpdateEntityStatusData = pydantic.Field(description="The status update data.")


# ----------------------------------------------------------------------------


DyffCommandType = Union[
    CreateChallengeTask,
    CreateChallengeTeam,
    CreateEntity,
    EditChallengeContent,
    EditChallengeTaskRules,
    EditEntityDocumentation,
    EditEntityLabels,
    EditFamilyMembers,
    EditTeam,
    ForgetEntity,
    RestoreEntity,
    UpdateEntityStatus,
]


__all__ = [
    "ChallengeContentPagePatch",
    "ChallengeContentPatch",
    "ChallengeTaskRulesExecutionEnvironmentPatch",
    "ChallengeTaskRulesSchedulePatch",
    "ChallengeTaskRulesPatch",
    "Command",
    "CreateChallengeTask",
    "CreateChallengeTaskAttributes",
    "CreateChallengeTaskData",
    "CreateChallengeTeam",
    "CreateChallengeTeamAttributes",
    "CreateChallengeTeamData",
    "CreateEntity",
    "DyffCommandType",
    "EditChallengeContent",
    "EditChallengeContentAttributes",
    "EditChallengeContentData",
    "EditChallengeContentPatch",
    "EditChallengeTaskRules",
    "EditChallengeTaskRulesAttributes",
    "EditChallengeTaskRulesData",
    "EditChallengeTaskRulesPatch",
    "EditEntityDocumentation",
    "EditEntityDocumentationAttributes",
    "EditEntityDocumentationData",
    "EditEntityDocumentationPatch",
    "EditEntityLabels",
    "EditEntityLabelsAttributes",
    "EditEntityLabelsData",
    "EditFamilyMembers",
    "EditFamilyMembersAttributes",
    "EditFamilyMembersData",
    "EditTeam",
    "EditTeamAttributes",
    "EditTeamData",
    "EntityIdentifier",
    "FamilyIdentifier",
    "ForgetEntity",
    "RestoreEntity",
    "RestoreEntityAttributes",
    "RestoreEntityData",
    "UpdateEntityStatus",
    "UpdateEntityStatusAttributes",
    "UpdateEntityStatusData",
]
