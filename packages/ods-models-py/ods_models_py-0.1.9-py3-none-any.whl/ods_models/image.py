"""
ODS Models - Image and Workflow Models
Image, workflow execution results, batches, and Kore execution models.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field
from ods_types import (
    ImageTypeEnum,
    ReviewStatusEnum,
    BatchTypeEnum,
    BatchStatusEnum,
    ExecutionStatusEnum,
)


class Image(BaseModel):
    """Image entity representing an uploaded or generated image"""
    id: str
    accountId: str
    studioId: str
    createdById: str
    name: str
    imgLocation: Dict[str, Any]  # {type: "s3", bucket: "bucket", key: "key"}
    imgUri: str
    imgUrls: Dict[str, str] = {"original": "", "thumbnail": ""}
    mimeType: str
    batchIds: List[str] = Field(default_factory=list)
    deleted: bool = False
    type: ImageTypeEnum = ImageTypeEnum.ORIGINAL
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    isReleased: bool = False
    size: int = 0
    width: int = 0
    height: int = 0
    isFavorite: bool = False
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)


class WorkflowExecutionResult(BaseModel):
    """Workflow execution result entity"""
    id: str
    batchId: str
    koreExecutionId: str
    originalImageId: str
    createdById: str
    studioId: str
    debugImageId: Optional[str] = None
    outputImageId: Optional[str] = None
    isPrimary: bool = False
    isFinal: bool = False
    reviewStatus: ReviewStatusEnum = ReviewStatusEnum.PENDING
    step: int = 0
    deleted: bool = False
    accountId: str = "00000000-0000-0000-0000-000000000000"
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)
    qaTaskToken: Optional[str] = None
    parentId: Optional[str] = None
    reviewerId: Optional[str] = None
    # Error handling fields
    errorCode: Optional[str] = None
    errorType: Optional[str] = None
    failureStage: Optional[str] = None
    remediationSuggestion: Optional[str] = None
    retryCount: int = 0


class WorkflowBatch(BaseModel):
    """Workflow batch entity"""
    id: str
    name: str
    accountId: str
    studioId: str
    createdById: str
    createdAt: datetime
    updatedAt: datetime
    workflowRegistryId: str
    inputParameters: Dict[str, Any] = Field(default_factory=dict)
    qaRequired: Dict[str, Any] = {"qaRequired": False}
    totalImages: int = 0
    success: int = 0
    failed: int = 0
    tags: List[str] = Field(default_factory=list)
    type: BatchTypeEnum = BatchTypeEnum.UPLOAD
    deleted: bool = False
    status: Optional[BatchStatusEnum] = None


class KoreExecution(BaseModel):
    """Kore execution entity"""
    id: str
    koreId: str
    koreName: str
    startTime: datetime
    accountId: str
    createdById: str
    studioId: str
    endTime: Optional[datetime] = None
    status: ExecutionStatusEnum = ExecutionStatusEnum.QUEUED
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)
    deleted: bool = False
    errorMsg: Optional[str] = None
    outputData: Optional[Dict[str, Any]] = None


@dataclass
class ResizeParams:
    """Resize parameters for image processing"""
    w: Optional[int] = None
    h: Optional[int] = None
    q: Optional[int] = None
    f: Optional[str] = None  # Format
    fit: Optional[str] = None  # Fit mode
    grayscale: Optional[bool] = None
    blur: Optional[int] = None
