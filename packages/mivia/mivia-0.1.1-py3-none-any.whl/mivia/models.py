"""Pydantic models for MiViA API."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(str, Enum):
    """Job status enum."""

    CACHED = "CACHED"
    NEW = "NEW"
    FAILED = "FAILED"
    PENDING = "PENDING"


class JobSource(str, Enum):
    """Job source enum."""

    WEB = "WEB"
    API = "API"
    SANDBOX = "SANDBOX"
    TEST = "TEST"
    IDENTIFICATION = "IDENTIFICATION"


class ModelAccessType(str, Enum):
    """Model access type enum."""

    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class ImageDto(BaseModel):
    """Image data transfer object."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    created_at: datetime = Field(alias="createdAt")
    filename: str
    thumbnail: str
    original_filename: str = Field(alias="orginalFilename")  # Note: server typo
    validated: bool
    placeholder: str | None = None
    width: int | None = None
    height: int | None = None


class ModelDto(BaseModel):
    """Model data transfer object."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    name: str
    display_name: str = Field(alias="displayName")
    access_type: ModelAccessType = Field(alias="accessType")
    is_default_visible: bool = Field(alias="isDefaultVisible")
    description_en: str | None = None
    description_de: str | None = None


class CustomizationNameDto(BaseModel):
    """Customization name in multiple languages."""

    en: str
    de: str


class CustomizationDto(BaseModel):
    """Customization data transfer object."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    name: CustomizationNameDto

    @property
    def name_en(self) -> str:
        """Get English name."""
        return self.name.en

    @property
    def name_de(self) -> str:
        """Get German name."""
        return self.name.de


class JobMaskDto(BaseModel):
    """Job mask data transfer object."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    parent_id: int | None = Field(None, alias="parentId")
    label: str
    filename: str
    is_submitted: bool = Field(alias="isSubmitted")


class JobFeedbackDto(BaseModel):
    """Job feedback data transfer object."""

    id: int
    rating: int
    comment: str


class JobCustomizationDto(BaseModel):
    """Job customization embedded object."""

    model_config = ConfigDict(populate_by_name=True)

    name_en: str = Field(alias="nameEn")
    name_de: str = Field(alias="nameDe")
    config: dict[str, Any] | None = None


class JobDto(BaseModel):
    """Job data transfer object (V2 and POST /jobs response)."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    image_id: UUID = Field(alias="imageId")
    model_id: UUID = Field(alias="modelId")
    result_id: UUID | None = Field(None, alias="resultId")
    status: JobStatus
    has_results: bool | None = Field(None, alias="hasResults")  # Only in GET /v2/jobs
    outdated: bool
    created_at: datetime = Field(alias="createdAt")
    image: str | None = None  # Only in GET /v2/jobs
    results: list[Any] | None = None
    user_feedback: JobFeedbackDto | None = Field(None, alias="userFeedback")
    masks: list[JobMaskDto] | None = None
    customization: JobCustomizationDto | None = None
    with_masks: bool = Field(alias="withMasks")


class PaginationDto(BaseModel):
    """Pagination metadata."""

    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    total_pages: int = Field(alias="totalPages")

    model_config = ConfigDict(populate_by_name=True)


class JobListResponse(BaseModel):
    """Response for job list endpoint."""

    data: list[JobDto]
    pagination: PaginationDto


class CreateJobsRequest(BaseModel):
    """Request body for creating jobs."""

    model_config = ConfigDict(populate_by_name=True)

    image_ids: list[UUID] = Field(serialization_alias="imageIds")
    model_id: UUID = Field(serialization_alias="modelId")
    customization_id: UUID | None = Field(None, serialization_alias="customizationId")
    source: JobSource = JobSource.API


class CreateReportRequest(BaseModel):
    """Request body for creating reports."""

    model_config = ConfigDict(populate_by_name=True)

    jobs_ids: list[UUID] = Field(serialization_alias="jobsIds")
    tz_offset: int | None = Field(None, serialization_alias="tzOffset")
    include_images: bool | None = Field(True, serialization_alias="includeImages")
