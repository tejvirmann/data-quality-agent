# Data Quality Agent

**Automated image quality gating for the Wisconsin Reading Center.**

## Impact

The Wisconsin Reading Center (UW-Madison, Dept of Ophthalmology) grades ~100,000 retinal images per year across multi-center clinical trials. Every image must meet quality standards before a human grader can assess it for disease markers.

**The problem:** Bad images (blurry, too dark, corrupted, wrong format) waste grader time, delay trial results, and force expensive patient retakes. A single ungradable image can cost 30+ minutes of technician time when you account for grading attempt, flagging, retake coordination, and re-imaging.

**The numbers:**
- ~100K images/year reviewed by WRC
- Even a 5% ungradable rate = 5,000 wasted review cycles/year
- At ~30 min per wasted cycle = **2,500 hours/year** of technician time lost to bad images
- Catching bad images at upload (before grading) eliminates this waste entirely
- This agent runs on a $20/month Vercel plan

**What this does:**
- Accepts a fundus image URL via MCP protocol
- Runs 7 classical quality checks (sharpness, resolution, format, illumination, color, corruption, metadata)
- Runs EyeQ/MCF-Net deep learning model for fundus-specific grading (Good / Usable / Reject)
- Returns an instant ACCEPT / REVIEW / REJECT verdict with detailed scores
- Plugs into any MCP-compatible assistant (OpenCode, Claude Desktop, etc.)

**Result:** Human graders only see images worth grading. Bad images are caught in seconds, not hours.

---

## Quick Start

```bash
make install        # Create venv + install deps
make fetch-model    # Download EyeQ model weights
make serve          # Run MCP server locally
make test           # Run tests
make clean          # Remove all Python artifacts
make deploy         # Deploy to Vercel
```

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
                                  +-- assess_fundus_quality (EyeQ DL model)
```

## MCP Tools

| Tool | What it checks | Output |
|---|---|---|
| `check_image_quality` | Runs all checks, returns verdict | ACCEPT / REVIEW / REJECT + full report |
| `check_sharpness` | Blur detection (Laplacian variance) | Score + pass/fail |
| `check_resolution` | Min dimensions (default 1024x1024) | Width, height, meets minimum |
| `check_format` | File type + corruption | Format name, valid, corrupted |
| `check_illumination` | Brightness, vignetting, exposure | Mean/std brightness, uniformity |
| `check_color` | RGB validation, channel balance | Color mode, balanced |
| `validate_metadata` | EXIF extraction | Metadata fields |
| `assess_fundus_quality` | EyeQ/MCF-Net deep learning | Good / Usable / Reject + confidence |

## Configuration

All quality thresholds are configurable via `QualityConfig` (Pydantic model) or environment variables:

```bash
QUALITY_MIN_WIDTH=2048
QUALITY_MIN_HEIGHT=2048
QUALITY_SHARPNESS_PASS=150
QUALITY_ALLOWED_FORMATS=JPEG,PNG,TIFF
```

## OpenCode Integration

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

## Tech Stack

- **Python** + **Pydantic** (all typed models)
- **FastMCP** (MCP server SDK, Streamable HTTP)
- **OpenCV** (headless) + **Pillow** (classical image checks)
- **PyTorch** + **EyeQ/MCF-Net** (fundus quality deep learning)
- **Vercel** serverless deployment

## License

EyeQ model weights are CC BY-NC-SA 4.0 (non-commercial use only).
