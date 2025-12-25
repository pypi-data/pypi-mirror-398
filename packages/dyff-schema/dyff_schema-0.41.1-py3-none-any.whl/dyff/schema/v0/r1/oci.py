# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import enum
import hashlib
from datetime import datetime, timezone
from typing import Any, Literal, Optional

import canonicaljson
import pydantic

from .base import int64


class KnownMediaTypes(str, enum.Enum):
    oci_image_manifest = "application/vnd.oci.image.manifest.v1+json"
    oci_image_config = "application/vnd.oci.image.config.v1+json"
    oci_image_layer_tar = "application/vnd.oci.image.layer.v1.tar"
    oci_image_layer_tar_gzip = "application/vnd.oci.image.layer.v1.tar+gzip"


# mypy gets confused because 'dict' is the name of a method in DyffBaseModel
_ModelAsDict = dict[str, Any]


class _OCISchemaBaseModel(pydantic.BaseModel):
    def model_dump(  # type: ignore [override]
        self, *, by_alias: bool = True, exclude_none: bool = True, **kwargs
    ) -> _ModelAsDict:
        return super().model_dump(
            by_alias=by_alias, exclude_none=exclude_none, **kwargs
        )

    def model_dump_json(  # type: ignore [override]
        self, *, by_alias: bool = True, exclude_none: bool = True, **kwargs
    ) -> str:
        return super().model_dump_json(
            by_alias=by_alias, exclude_none=exclude_none, **kwargs
        )

    def dict(
        self, *, by_alias: bool = True, exclude_none: bool = True, **kwargs
    ) -> _ModelAsDict:
        return self.model_dump(by_alias=by_alias, exclude_none=exclude_none, **kwargs)

    def json(
        self, *, by_alias: bool = True, exclude_none: bool = True, **kwargs
    ) -> str:
        return self.model_dump_json(
            by_alias=by_alias, exclude_none=exclude_none, **kwargs
        )

    @pydantic.model_validator(mode="after")
    def _ensure_datetime_timezone_utc(self):
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, datetime):
                if field_value.tzinfo is None:
                    # Set UTC timezone for naive datetime
                    setattr(self, field_name, field_value.replace(tzinfo=timezone.utc))
                elif field_value.tzinfo != timezone.utc:
                    # Convert to UTC timezone
                    setattr(self, field_name, field_value.astimezone(timezone.utc))
        return self


class _DigestMixin(pydantic.BaseModel):
    def digest(self) -> str:
        obj = self.model_dump(mode="json")
        h = hashlib.sha256(usedforsecurity=False)
        for chunk in canonicaljson.iterencode_canonical_json(obj):
            h.update(chunk)
        return "sha256:{}".format(h.hexdigest())


class Platform(_OCISchemaBaseModel):
    architecture: str
    os: str
    os_version: Optional[str] = pydantic.Field(alias="os.version", default=None)
    os_features: Optional[list[str]] = pydantic.Field(alias="os.features", default=None)
    variant: Optional[str] = pydantic.Field(default=None)


class Descriptor(_OCISchemaBaseModel):
    """
    https://github.com/opencontainers/image-spec/blob/v1.1.1/descriptor.md
    """

    mediaType: str = pydantic.Field()
    digest: str = pydantic.Field()
    size: int64() = pydantic.Field(  # type: ignore
        description="This REQUIRED property specifies the size, in bytes,"
        " of the raw content. This property exists so that a client"
        " will have an expected size for the content before processing."
        " If the length of the retrieved content does not match"
        " the specified length, the content SHOULD NOT be trusted."
    )
    urls: Optional[list[str]] = pydantic.Field(default=None)
    annotations: Optional[dict[str, str]] = pydantic.Field(default=None)
    data: Optional[str] = pydantic.Field(default=None)
    artifactType: Optional[str] = pydantic.Field(default=None)

    @staticmethod
    def empty() -> Descriptor:
        """
        https://github.com/opencontainers/image-spec/blob/v1.1.1/manifest.md#guidance-for-an-empty-descriptor
        """
        return Descriptor.model_validate(
            {
                "mediaType": "application/vnd.oci.empty.v1+json",
                "digest": "sha256:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
                "size": 2,
                "data": "e30=",
            }
        )


class ImageDescriptor(Descriptor):
    platform: Platform


class ExecutionParameters(_OCISchemaBaseModel):
    # TODO
    pass


class RootFS(_OCISchemaBaseModel):
    type_: Literal["layers"] = pydantic.Field(alias="type", default="layers")
    diff_ids: list[str] = pydantic.Field()


class HistoryEntry(_OCISchemaBaseModel):
    created: Optional[str] = pydantic.Field(default=None)
    author: Optional[str] = pydantic.Field(default=None)
    created_by: Optional[str] = pydantic.Field(default=None)
    comment: Optional[str] = pydantic.Field(default=None)
    empty_layer: Optional[bool] = pydantic.Field(default=None)


class ImageConfig(Platform, _DigestMixin):
    """
    https://github.com/opencontainers/image-spec/blob/v1.1.1/config.md
    """

    created: Optional[str] = pydantic.Field(default=None)
    author: Optional[str] = pydantic.Field(default=None)
    config: Optional[ExecutionParameters] = pydantic.Field(default=None)
    rootfs: RootFS
    history: Optional[list[HistoryEntry]] = pydantic.Field(default=None)


class ImageManifest(_OCISchemaBaseModel):
    schemaVersion: Literal["2"] = "2"
    mediaType: Literal["application/vnd.oci.image.manifest.v1+json"] = (
        "application/vnd.oci.image.manifest.v1+json"
    )
    artifactType: Optional[str] = pydantic.Field(default=None)
    config: Descriptor = pydantic.Field(default_factory=Descriptor.empty)
    layers: list[Descriptor] = pydantic.Field(
        default_factory=lambda: [Descriptor.empty()]
    )
    subject: Optional[Descriptor] = pydantic.Field(default=None)
    annotations: Optional[dict[str, str]] = pydantic.Field(default=None)

    def is_image_manifest(self) -> bool:
        return self.artifactType is None

    def is_artifact_manifest(self) -> bool:
        return self.artifactType is not None

    @pydantic.model_validator(mode="after")
    def validate_types(self):
        if self.artifactType is None:
            if self.config.mediaType != KnownMediaTypes.oci_image_config.value:
                raise ValueError(
                    ".config.mediaType must be"
                    f"{KnownMediaTypes.oci_image_config.value}"
                    " if .artifactType is unspecified"
                )
        return self


__all__ = [
    "Descriptor",
    "ExecutionParameters",
    "HistoryEntry",
    "ImageConfig",
    "ImageDescriptor",
    "ImageManifest",
    "Platform",
    "RootFS",
]
