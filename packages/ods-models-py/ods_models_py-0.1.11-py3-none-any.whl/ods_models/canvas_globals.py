"""
ODS Models - Canvas Globals
Global canvas configuration including presets, guides, and grids.
Python equivalent of canvas globals from design-data-microservices.
"""

from typing import List, Dict, Optional, Union
from pydantic import BaseModel
from ods_types import CanvasGuideKind, CanvasGridKind, BentoAxis


class FlexPreset(BaseModel):
    """Canvas aspect ratio preset"""
    canvas_width: float
    canvas_height: float
    label: str
    id: str


class CanvasGuides(BaseModel):
    """Canvas guide definition"""
    id: str
    name: str
    slot_key: str
    cases: Optional[Dict[str, Dict[str, float]]] = None
    x1: float
    y1: float
    x2: float
    y2: float
    layer_id: Optional[str] = None
    is_point: Optional[bool] = None
    kind: CanvasGuideKind
    dir: Optional[Dict[str, float]] = None


class CanvasGridBase(BaseModel):
    """Base class for canvas grids"""
    kind: CanvasGridKind
    id: str


class CanvasSimpleGridDef(CanvasGridBase):
    """
    Simple (bootstrap-style) grid definition.
    All margin/gutter values are normalized 0–1 relative to the parent box.
    """
    kind: CanvasGridKind = CanvasGridKind.SIMPLE
    columns: int
    rows: Optional[int] = None
    marginX: Optional[float] = None
    marginY: Optional[float] = None
    gutterX: Optional[float] = None
    gutterY: Optional[float] = None


class CanvasBentoNode(BaseModel):
    """
    Node inside a nested Bento grid.
    - type: 'row' → siblings split vertically (height)
    - type: 'col' → siblings split horizontally (width)
    - size: weight within the sibling group
    """
    id: str
    type: BentoAxis
    size: float
    children: Optional[List["CanvasBentoNode"]] = None


class CanvasBentoGridDef(CanvasGridBase):
    """Top-level Bento grid definition"""
    kind: CanvasGridKind = CanvasGridKind.BENTO
    root: List[CanvasBentoNode]


# Union type for grid definitions
CanvasGridDef = Union[CanvasSimpleGridDef, CanvasBentoGridDef]


class CanvasGlobals(BaseModel):
    """
    Global canvas configuration.
    Contains flex presets, guides, and optional grid definitions.
    """
    flex_presets: Dict[str, FlexPreset]
    canvas_guides: List[CanvasGuides]
    canvas_grids: Optional[List[CanvasGridDef]] = None


# Update forward references for recursive model
CanvasBentoNode.model_rebuild()
