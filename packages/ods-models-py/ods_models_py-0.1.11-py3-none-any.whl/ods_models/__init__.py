"""
ODS Models - Python Implementation
Pydantic data models for the ODS (Optikka Design System).
Python equivalent of @optikka/ods-models npm package.
"""

__version__ = "0.1.2"

# Re-export base enums from ods-types (via base.py for convenience)
from ods_models.base import (
    ImageMimeType,
    ReviewStatusEnum,
    ImageTypeEnum,
    BatchTypeEnum,
    BatchStatusEnum,
    ExecutionStatusEnum,
    DesignDataInputTypes,
    HTTPMethod,
    TextType,
    CanvasGuideKind,
    CanvasGridKind,
    BentoAxis,
    RenderRunStatus,
    RenderRunQueueEventType,
    TargetInputJobStatus,
    ColorType,
    BrandRuleType,
    BrandRuleTarget,
    DataType,
)

# Re-export guides
from ods_models.guides import GuideDoc

# Re-export canvas globals
from ods_models.canvas_globals import (
    FlexPreset,
    CanvasGuides,
    CanvasGridBase,
    CanvasSimpleGridDef,
    CanvasBentoNode,
    CanvasBentoGridDef,
    CanvasGridDef,
    CanvasGlobals,
)

# Re-export input parameters
from ods_models.input_parameters import (
    AssetSpecs,
    LogoSpecs,
    TextSpecs,
    GroupSpecs,
    InputParameters,
    InputParametersPartialForCreate,
)

# Re-export template input
from ods_models.template_input import (
    Asset,
    Logo,
    Text,
    InputGroup,
    TemplateInputDesignData,
    TemplateInput,
    TemplateInputWithoutId,
    TemplateInputForCreate,
)

# Re-export template registry
from ods_models.template_registry import (
    TemplateRegistry,
    TemplateRegistryWithoutId,
    TemplateRegistryInputForCreate,
    ODSScript,
    TemplateRecipe,
    # API body models
    AddAssetToTemplateRegistryBody,
    AddTextToTemplateRegistryBody,
    AddLogoToTemplateRegistryBody,
    AddGroupToTemplateRegistryBody,
    AddExtraDataToTemplateRegistryBody,
    RemoveExtraDataFromTemplateRegistryBody,
    AddFlexPresetToTemplateRegistryBody,
    UpdateStudioAndAccountIdsForTemplateRegistryBody,
    UpdateTemplatePreviewImageBody,
    UpdateDefaultValueBody,
)

# Re-export render run
from ods_models.render_run import (
    RenderRun,
    RenderRunInputForCreate,
    RenderRunWithoutId,
    StartRenderRunFromTargetInputJobInput,
    TargetInputJobImage,
    Progress,
    Mapping,
    TargetInputJobResult,
    TargetInputJob,
)

# Re-export image and workflow models
from ods_models.image import (
    Image,
    WorkflowExecutionResult,
    WorkflowBatch,
    KoreExecution,
    ResizeParams,
)

# Re-export brand models
from ods_models.brand import (
    RGB,
    HSL,
    HSV,
    CMYK,
    Color,
    ColorPalette,
    BrandRule,
    ImageQueryHint,
    EntityAttributeSpec,
    BrandRegistry,
    BrandRegistryWithoutId,
    BrandRegistryInputForCreate,
    Brand,
    BrandWithoutId,
    BrandInputForCreate,
    BrandInputWithoutId,
)

__all__ = [
    # Base enums (re-exported from ods-types)
    "ImageMimeType",
    "ReviewStatusEnum",
    "ImageTypeEnum",
    "BatchTypeEnum",
    "BatchStatusEnum",
    "ExecutionStatusEnum",
    "DesignDataInputTypes",
    "HTTPMethod",
    "TextType",
    "CanvasGuideKind",
    "CanvasGridKind",
    "BentoAxis",
    "RenderRunStatus",
    "RenderRunQueueEventType",
    "TargetInputJobStatus",
    "ColorType",
    "BrandRuleType",
    "BrandRuleTarget",
    "DataType",
    # Guides
    "GuideDoc",
    # Canvas globals
    "FlexPreset",
    "CanvasGuides",
    "CanvasGridBase",
    "CanvasSimpleGridDef",
    "CanvasBentoNode",
    "CanvasBentoGridDef",
    "CanvasGridDef",
    "CanvasGlobals",
    # Input parameters
    "AssetSpecs",
    "LogoSpecs",
    "TextSpecs",
    "GroupSpecs",
    "InputParameters",
    "InputParametersPartialForCreate",
    # Template input
    "Asset",
    "Logo",
    "Text",
    "InputGroup",
    "TemplateInputDesignData",
    "TemplateInput",
    "TemplateInputWithoutId",
    "TemplateInputForCreate",
    # Template registry
    "TemplateRegistry",
    "TemplateRegistryWithoutId",
    "TemplateRegistryInputForCreate",
    "ODSScript",
    "TemplateRecipe",
    # Template registry API body models
    "AddAssetToTemplateRegistryBody",
    "AddTextToTemplateRegistryBody",
    "AddLogoToTemplateRegistryBody",
    "AddGroupToTemplateRegistryBody",
    "AddExtraDataToTemplateRegistryBody",
    "RemoveExtraDataFromTemplateRegistryBody",
    "AddFlexPresetToTemplateRegistryBody",
    "UpdateStudioAndAccountIdsForTemplateRegistryBody",
    "UpdateTemplatePreviewImageBody",
    "UpdateDefaultValueBody",
    # Render run
    "RenderRun",
    "RenderRunInputForCreate",
    "RenderRunWithoutId",
    "StartRenderRunFromTargetInputJobInput",
    "TargetInputJobImage",
    "Progress",
    "Mapping",
    "TargetInputJobResult",
    "TargetInputJob",
    # Image and workflow
    "Image",
    "WorkflowExecutionResult",
    "WorkflowBatch",
    "KoreExecution",
    "ResizeParams",
    # Brand models
    "RGB",
    "HSL",
    "HSV",
    "CMYK",
    "Color",
    "ColorPalette",
    "BrandRule",
    "ImageQueryHint",
    "EntityAttributeSpec",
    "BrandRegistry",
    "BrandRegistryWithoutId",
    "BrandRegistryInputForCreate",
    "Brand",
    "BrandWithoutId",
    "BrandInputForCreate",
    "BrandInputWithoutId",
]
