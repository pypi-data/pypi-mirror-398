"""
ODS Models - Guides
Guide document structures for canvas guides.
Python equivalent of @optikka/ods-models/guides
"""

from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class GuideDoc(BaseModel):
    """
    Guide document from optikore/mongo.
    Represents a rectangular guide region with metadata.
    Matches design-data-microservices Python models (source of truth).
    """
    name: str
    fit: Dict[str, Any] = Field(description="Contains x1, y1, x2, y2 coordinates")
    _id: Optional[str] = None
    imageId: Optional[str] = None
    werId: Optional[str] = None
    extraData: Optional[Dict[str, Any]] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
