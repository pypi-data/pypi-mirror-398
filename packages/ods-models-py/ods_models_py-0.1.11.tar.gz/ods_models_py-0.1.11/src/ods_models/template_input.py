"""
ODS Models - Template Input
Template input data structures (assets, logos, texts).
Python equivalent of template input from design-data-microservices.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
from ods_types import ImageMimeType
from ods_models.guides import GuideDoc


class Asset(BaseModel):
    """
    Asset data structure.
    Represents an image asset with metadata and guides.
    parsing_label is optional to support items in groups (which use the group's parsing_label).
    """
    id: Optional[str] = None
    width: int
    height: int
    mime_type: ImageMimeType
    parsing_label: Optional[str] = None
    guides: Optional[List[GuideDoc]] = []
    original_image_id: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None
    s3Location: Dict[str, Any] = {}
    wer_ids: Optional[List[str]] = None
    workflow_registry_ids: Optional[List[str]] = None


class Logo(BaseModel):
    """
    Logo data structure.
    Represents a logo image with metadata and guides.
    parsing_label is optional to support items in groups (which use the group's parsing_label).
    """
    image_id: Optional[str] = None
    name: Optional[str] = None
    mime_type: ImageMimeType
    width: int
    height: int
    parsing_label: Optional[str] = None
    s3Location: Dict[str, Any] = {}
    guides: Optional[List[GuideDoc]] = None
    description: Optional[str] = None
    wer_id: Optional[str] = None
    workflow_registry_id: Optional[str] = None


class Text(BaseModel):
    """
    Text data structure.
    Represents a text input with localization support.
    parsing_label is optional to support items in groups (which use the group's parsing_label).
    """
    id: Optional[str] = None
    value: str
    parsing_label: Optional[str] = None
    isoCode: str


class InputGroup(BaseModel):
    """
    Input group structure.
    Groups multiple items (assets and logos) under a single parsing_label.
    Items can be mixed types (Asset or Logo) in the same array.
    Note: Items in groups do NOT have parsing_label - only the group itself has parsing_label.
    Items use the group's parsing_label when processed.
    Note: Groups only support Asset and Logo items, not Text items.
    """
    parsing_label: str
    items: List[Union[Asset, Logo]]


class TemplateInputDesignData(BaseModel):
    """
    Template input design data structure.
    Contains all assets, logos, texts, groups, and extra data for a template.
    """
    assets: List[Asset] = []
    logos: List[Logo] = []
    texts: List[Text] = []
    groups: Optional[InputGroup] = None  # Single optional group with parsing_label and items (Asset/Logo only)
    extra_data: Dict[str, Any] = {}


class TemplateInput(BaseModel):
    """
    Template input object (a template input instance validated against a template registry).
    Represents a complete set of design data for rendering.
    """
    id: str
    template_registry_id: str
    inputs: TemplateInputDesignData
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_by: str
    account_id: str
    studio_id: str
    tags: List[str] = Field(default_factory=list)
    name: Optional[str] = None
    canvas_key: Optional[str] = None


class TemplateInputWithoutId(BaseModel):
    """Template input for insert operations (no id field)"""
    template_registry_id: str
    inputs: TemplateInputDesignData
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str
    created_by: str
    account_id: str
    studio_id: str
    tags: List[str] = Field(default_factory=list)
    name: Optional[str] = None
    canvas_key: Optional[str] = None


class TemplateInputForCreate(BaseModel):
    """Partial template input for create operations"""
    template_registry_id: str
    inputs: TemplateInputDesignData
    created_by: str
    account_id: str
    studio_id: str
    tags: List[str] = Field(default_factory=list)
    name: Optional[str] = None
    canvas_key: Optional[str] = None
