# ods-models-py

Pydantic data models for the ODS (Optikka Design System) - Python implementation.

This is the Python equivalent of the `@optikka/ods-models` npm package, providing Pydantic models for templates, inputs, render runs, and related entities.

## Installation

```bash
pip install ods-models-py
```

## Usage

```python
from ods_models import (
    TemplateRegistry,
    TemplateInput,
    Asset,
    Logo,
    Text,
    ImageMimeType,
    RenderRun,
    RenderRunStatus,
)

# Create an asset
asset = Asset(
    width=1920,
    height=1080,
    mime_type=ImageMimeType.PNG,
    parsing_label="hero_image",
    s3Location={"bucket": "my-bucket", "key": "image.png"},
)

# Create template input design data
from ods_models import TemplateInputDesignData

design_data = TemplateInputDesignData(
    assets=[asset],
    logos=[],
    texts=[],
    extra_data={},
)

# Use with validation
template_input = TemplateInput(
    id="123",
    template_registry_id="template-456",
    inputs=design_data,
    created_by="user@example.com",
    updated_by="user@example.com",
    account_id="account-789",
    studio_id="studio-101",
)
```

## Package Contents

### Base Enums
- `ImageMimeType` - Supported image MIME types
- `ReviewStatusEnum` - Review status for workflows
- `ImageTypeEnum` - Image type classification
- `BatchTypeEnum`, `BatchStatusEnum` - Workflow batch types
- `ExecutionStatusEnum` - Kore execution status

### Models

#### Template System
- `TemplateRegistry` - Template metadata and configuration
- `TemplateInput` - Template input with design data
- `Asset`, `Logo`, `Text` - Design data elements
- `InputParameters` - Template input specifications
- `CanvasGlobals` - Canvas configuration (presets, guides, grids)

#### Rendering
- `RenderRun` - Batch rendering operations
- `TargetInputJob` - Target input job processing

#### Images & Workflows
- `Image` - Image entity
- `WorkflowExecutionResult` - Workflow execution results
- `WorkflowBatch` - Workflow batch entity
- `KoreExecution` - Kore execution entity

#### Supporting Models
- `GuideDoc` - Canvas guide definitions
- `FlexPreset` - Canvas aspect ratio presets
- `AssetSpecs`, `LogoSpecs`, `TextSpecs` - Input specifications

## Features

✅ **Type Safety**: Full Pydantic validation with Python type hints
✅ **Compatible**: Matches TypeScript models in `@optikka/ods-models`
✅ **Validated**: Runtime validation with Pydantic v2
✅ **Documented**: Comprehensive docstrings and examples

## Dependencies

- `pydantic>=2.6.1,<3.0.0`
- `ods-types-py>=0.1.0,<1.0.0`

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Related Packages

- `ods-types-py` - Core types and enums
- `optikka-design-data-layer` - AWS utilities and clients

## License

PROPRIETARY - Optikka
