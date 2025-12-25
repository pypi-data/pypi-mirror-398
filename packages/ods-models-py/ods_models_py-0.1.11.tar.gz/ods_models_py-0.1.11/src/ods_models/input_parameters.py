"""
ODS Models - Input Parameters
Specifications for template input requirements (assets, texts, logos).
Python equivalent of input parameters from design-data-microservices.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ods_types import ImageMimeType, TextType


class AssetSpecs(BaseModel):
    """
    Schema for individual asset specifications.
    Defines requirements for asset inputs in a template.
    """
    workflow_registry_id: Optional[str] = None
    workflow_required: bool = False
    allowed_types: List[ImageMimeType]
    min_width: int
    min_height: int
    max_width: int
    max_height: int
    guides_required: Optional[List[str]] = None  # guide names
    description: Optional[str] = None
    name: Optional[str] = None
    parsing_label: str
    optional: bool = False  # Whether this input can be omitted
    should_validate: bool = Field(default=True, alias="validate", serialization_alias="validate")  # Whether to apply dimension/type validation
    default_value: Optional[str] = None  # URL or path to default image for consumption app UI


class LogoSpecs(AssetSpecs):
    """
    Schema for individual logo specifications.
    Identical to AssetSpecs but semantically different.
    """
    pass


class TextSpecs(BaseModel):
    """
    Schema for individual text specifications.
    Defines requirements for text inputs in a template.
    """
    workflow_registry_id: Optional[str] = None
    workflow_required: bool = False
    max_chars: int
    min_chars: int
    type: TextType
    parsing_label: str
    name: str
    description: str
    options: Optional[List[str]] = None  # if type==select
    container: Optional[str] = None
    optional: bool = False  # Whether this input can be omitted
    should_validate: bool = Field(default=True, alias="validate", serialization_alias="validate")  # Whether to apply char limit/type validation
    default_value: Optional[str] = None  # Default text value for consumption app UI


class GroupSpecs(BaseModel):
    """
    Schema for group specifications.
    Groups allow multiple items (assets, logos, texts) to be organized together.
    """
    parsing_label: str
    optional: bool = False  # Whether this group can be omitted


class InputParameters(BaseModel):
    """
    All input specifications for a template.
    Defines what assets, texts, logos, and groups are required.
    """
    assets: List[AssetSpecs]
    texts: List[TextSpecs]
    logos: List[LogoSpecs]
    groups: List[GroupSpecs] = []
    extra_data: Optional[Dict[str, Any]] = None


class InputParametersPartialForCreate(BaseModel):
    """
    Partial input parameters for create operations.
    All fields optional with defaults.
    """
    assets: List[AssetSpecs] = []
    texts: List[TextSpecs] = []
    logos: List[LogoSpecs] = []
    groups: List[GroupSpecs] = []
    extra_data: Optional[Dict[str, Any]] = {}
