# Data Quality Agent — Plan

## Overview

An MCP server deployed on Vercel that accepts eye/fundus images and runs automated quality checks for the Wisconsin Reading Center. The server exposes tools via the Model Context Protocol (Streamable HTTP transport) so any MCP-compatible assistant (OpenCode, Claude Desktop, etc.) can plug in and use it.

Uses **Pydantic** throughout for all inputs, outputs, and config. Includes a deep learning fundus quality model (**EyeQ/MCF-Net**) alongside classical CV checks.

---

## Context: Wisconsin Reading Center

The WRC (University of Wisconsin-Madison, Dept of Ophthalmology) grades ~100K retinal images/year for clinical trials. They assess: focus/clarity, illumination, field definition, color balance, and overall gradability. Images that fail quality thresholds trigger retake requests. This agent automates that first-pass quality gate.

---

## Architecture

```
[MCP Client]                    [Vercel Serverless]
 OpenCode / Claude Desktop       Python + FastMCP + Pydantic
 or any MCP client          -->  /api/mcp endpoint
                                  |
                                  +-- check_image_quality (orchestrator)
                                  +-- check_sharpness
                                  +-- check_resolution
                                  +-- check_format
                                  +-- check_illumination
                                  +-- check_color
                                  +-- validate_metadata
                                  +-- assess_fundus_quality (EyeQ deep learning)
```

**Transport**: Streamable HTTP (single POST endpoint at `/api/mcp`)
**Runtime**: Python on Vercel (`@vercel/python`)
**Image input**: Images passed by URL (not inline) to avoid the 4.5MB Vercel payload limit. The server fetches and processes the image.

---

## Tech Stack

| Component | Choice | Why |
|---|---|---|
| MCP Framework | `mcp` (FastMCP) | Official Python SDK, decorator-based, Streamable HTTP support |
| Data Models | `pydantic` | All inputs, outputs, config are typed Pydantic models |
| Image Processing | `opencv-python-headless` | Blur detection (Laplacian), illumination analysis |
| Image I/O | `Pillow` | Resolution, format, corruption, color space, metadata |
| Deep Learning | `torch` + EyeQ/MCF-Net | Fundus-specific quality: Good/Usable/Reject (DenseNet121) |
| HTTP | `httpx` | Async image fetching from URLs |
| Deployment | Vercel + `@vercel/python` | Matches existing project patterns |
| Build | `Makefile` | Standard commands for dev, test, clean, deploy |

---

## Deep Learning Model: EyeQ / MCF-Net

**Why EyeQ**: Only fundus quality model with published pretrained weights, clear 3-class output (Good/Usable/Reject), and a real codebase. Based on DenseNet121 with multi-color-space fusion.

**How it works**:
1. Input image is converted to 3 color spaces (RGB, HSV, LAB)
2. Each variant is resized to 224x224, normalized with ImageNet stats
3. MCF-Net (DenseNet121 backbone) processes all 3 and fuses features
4. Outputs softmax probabilities over 3 classes: Good, Usable, Reject

**Weights**: ~112MB, downloaded from OneDrive link in EyeQ repo. Bundled or fetched at cold start.

**Constraint**: Adds ~200MB to lambda (PyTorch + weights). Will need `maxLambdaSize: 250mb` or serve model from external storage. May push past Vercel free tier — we'll handle this with a fallback: if torch isn't available, skip the DL check and rely on classical checks only.

---

## MCP Tools (8 tools)

All tool inputs and outputs are **Pydantic models**.

### 1. `check_image_quality` (main orchestrator)
- **Input**: `ImageInput(image_url: HttpUrl)`
- **Output**: `QualityReport(verdict: Verdict, checks: list[CheckResult], fundus_assessment: FundusAssessment | None)`
- Runs all checks below and returns combined assessment
- Overall verdict: `ACCEPT`, `REVIEW`, or `REJECT` (enum)

### 2. `check_sharpness`
- Laplacian variance on grayscale image
- **Output**: `SharpnessResult(score: float, is_sharp: bool, detail: str)`

### 3. `check_resolution`
- Validates width/height against minimums (default: 1024x1024)
- **Output**: `ResolutionResult(width: int, height: int, meets_minimum: bool, megapixels: float)`

### 4. `check_format`
- Validates file type from magic bytes, corruption detection
- **Output**: `FormatResult(format: str, valid: bool, corrupted: bool)`

### 5. `check_illumination`
- Brightness histogram, vignetting, exposure analysis
- **Output**: `IlluminationResult(mean_brightness: float, std_brightness: float, uniform: bool, vignetting_detected: bool)`

### 6. `check_color`
- RGB validation, channel balance
- **Output**: `ColorResult(mode: str, channels: int, balanced: bool, channel_means: list[float])`

### 7. `validate_metadata`
- EXIF extraction
- **Output**: `MetadataResult(has_exif: bool, fields: dict[str, str])`

### 8. `assess_fundus_quality`
- EyeQ/MCF-Net deep learning inference
- **Output**: `FundusAssessment(grade: FundusGrade, confidence: float, probabilities: dict[str, float])`
- `FundusGrade` enum: `GOOD`, `USABLE`, `REJECT`

---

## Pydantic Models (src/models.py)

```python
class Verdict(str, Enum):
    ACCEPT = "accept"
    REVIEW = "review"
    REJECT = "reject"

class FundusGrade(str, Enum):
    GOOD = "good"
    USABLE = "usable"
    REJECT = "reject"

class ImageInput(BaseModel):
    image_url: HttpUrl

class SharpnessResult(BaseModel):
    score: float
    is_sharp: bool
    detail: str

class ResolutionResult(BaseModel):
    width: int
    height: int
    meets_minimum: bool
    megapixels: float

# ... etc for each check

class FundusAssessment(BaseModel):
    grade: FundusGrade
    confidence: float
    probabilities: dict[str, float]

class CheckResult(BaseModel):
    name: str
    passed: bool
    detail: str

class QualityReport(BaseModel):
    verdict: Verdict
    checks: list[CheckResult]
    fundus_assessment: FundusAssessment | None = None

class QualityConfig(BaseModel):
    sharpness_threshold: float = 100.0
    min_width: int = 1024
    min_height: int = 1024
    # ... all thresholds as fields with defaults
```

---

## Clean Python Project Setup

The "remnants" problem is `__pycache__/` directories and `.pyc` bytecode files that Python creates at runtime. Solution:

1. **`.gitignore`** — excludes all Python artifacts
2. **`Makefile clean` target** — deletes `__pycache__`, `.pyc`, `.pyo`, `.egg-info`, `.mypy_cache`, etc.
3. **`pyproject.toml`** — modern Python packaging (no `setup.py`)
4. **`.python-version`** — pins Python version
5. **Virtual environment** — isolated deps via `python -m venv .venv`

---

## Project Structure

```
data-quality-agent/
  api/
    mcp.py                  # Vercel serverless entry — MCP endpoint
  src/
    __init__.py
    server.py               # FastMCP server definition + tool registration
    models.py               # All Pydantic models (inputs, outputs, config)
    config.py               # QualityConfig defaults + env overrides
    image_loader.py         # Fetch image from URL via httpx
    checks/
      __init__.py
      sharpness.py          # Laplacian blur detection
      resolution.py         # Dimension validation
      format_check.py       # Format + corruption checks (not format.py — shadows stdlib)
      illumination.py       # Brightness/vignetting analysis
      color.py              # Color space validation
      metadata.py           # EXIF extraction
    ml/
      __init__.py
      eyeq.py              # EyeQ/MCF-Net inference wrapper
      models/               # Pretrained weights (gitignored, fetched on first run)
  tests/
    __init__.py
    conftest.py             # Shared fixtures
    test_checks.py          # Unit tests for each check
    test_models.py          # Pydantic model tests
    test_server.py          # MCP tool integration tests
    fixtures/               # Sample test images
  Makefile
  pyproject.toml            # Modern Python packaging + deps
  requirements.txt          # Vercel needs this for deployment
  vercel.json
  .gitignore
  .python-version
  README.md
  plan.md
```

---

## Makefile

```makefile
.PHONY: install dev test lint clean serve deploy

# Create venv and install deps
install:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt

# Install with dev deps (pytest, mypy, ruff)
dev:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt -r requirements-dev.txt

# Run tests
test:
	.venv/bin/pytest tests/ -v

# Lint + type check
lint:
	.venv/bin/ruff check src/ tests/
	.venv/bin/mypy src/

# Remove all Python artifacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf dist/ build/

# Run MCP server locally
serve:
	.venv/bin/python -m src.server

# Deploy to Vercel
deploy:
	vercel --prod

# Download EyeQ model weights
fetch-model:
	.venv/bin/python -m src.ml.eyeq --download
```

---

## vercel.json

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/mcp.py",
      "use": "@vercel/python",
      "config": { "maxLambdaSize": "250mb" }
    }
  ],
  "routes": [
    { "src": "/mcp(.*)", "dest": "/api/mcp.py" }
  ],
  "functions": {
    "api/mcp.py": { "maxDuration": 60 }
  }
}
```

- `maxLambdaSize: 250mb` — OpenCV + PyTorch + model weights
- `maxDuration: 60` — DL inference + image fetch needs time (requires Pro tier)
- Route `/mcp` to the Python handler

---

## Implementation Phases

### Phase 1: Project Scaffolding
1. Set up clean project: `pyproject.toml`, `.gitignore`, `.python-version`, `Makefile`, `vercel.json`
2. Define all Pydantic models in `src/models.py`
3. Implement `src/config.py` with `QualityConfig` (Pydantic settings)
4. Implement `src/image_loader.py` (fetch image from URL)

### Phase 2: Classical Quality Checks
5. Implement each check module returning Pydantic results
6. Wire up the orchestrator `check_image_quality`
7. Write unit tests with sample images
8. CLI test script to drop in an image URL and get a report

### Phase 3: EyeQ Deep Learning
9. Port EyeQ/MCF-Net inference to `src/ml/eyeq.py`
10. Add `fetch-model` Makefile target to download weights
11. Integrate as `assess_fundus_quality` tool
12. Graceful fallback if torch unavailable

### Phase 4: MCP Server + Deploy
13. Set up FastMCP server in `src/server.py` with all 8 tools
14. Create Vercel entry point `api/mcp.py`
15. Test locally with `mcp dev`
16. Deploy to Vercel, verify `/mcp` endpoint

### Phase 5: Assistant Integration
17. Configure OpenCode to connect to deployed MCP server
18. Test end-to-end: send image URL via assistant -> get quality report
19. Add example `opencode.json` config to repo

---

## Quality Thresholds (defaults, tunable via QualityConfig)

| Check | Pass | Review | Fail |
|---|---|---|---|
| Sharpness (Laplacian var) | > 150 | 80-150 | < 80 |
| Resolution | >= 1024x1024 | >= 512x512 | < 512x512 |
| Brightness mean | 60-200 | 40-60 or 200-230 | < 40 or > 230 |
| Brightness std (uniformity) | < 60 | 60-80 | > 80 |
| Color balance (channel diff) | < 30 | 30-50 | > 50 |
| Format | Allowed list | — | Not in list or corrupted |
| EyeQ grade | Good | Usable | Reject |

---

## OpenCode Integration Example

```json
{
  "mcp": {
    "data-quality": {
      "type": "remote",
      "url": "https://data-quality-agent.vercel.app/mcp",
      "enabled": true
    }
  }
}
```

---

## Constraints & Notes

- **Vercel Pro likely needed**: PyTorch + model weights push past free tier limits (10s timeout, 50MB lambda). Pro gives 60s timeout and 250MB lambda.
- **Fallback mode**: If torch isn't available (e.g., free tier), skip EyeQ and rely on classical checks only. The orchestrator handles this gracefully.
- **Image size**: Images passed by URL, not inline (Vercel 4.5MB payload limit). The server fetches the image via `httpx`.
- **OpenCV on Vercel**: Use `opencv-python-headless` to avoid GUI dependencies.
- **EyeQ license**: CC BY-NC-SA 4.0 (non-commercial only). Fine for research/academic use at WRC.
- **Clean builds**: `.gitignore` covers all Python artifacts. `make clean` removes everything. No `.pyc` remnants across branches.

---

## Future Enhancements

- **Field-of-view detection**: Check if macula/optic disc is properly centered
- **DICOM support**: Parse DICOM headers for medical imaging metadata
- **Batch processing endpoint**: Accept a list of URLs, return bulk results
- **Dashboard**: Simple web UI showing quality stats over time
- **Webhook notifications**: Alert when images fail quality
