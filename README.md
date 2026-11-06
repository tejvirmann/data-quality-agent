<p align="center">
  <img src="https://em-content.zobj.net/source/apple/391/eye_1f441-fe0f.png" width="80" alt="eye" />
</p>

<h1 align="center">Data Quality Agent</h1>

<p align="center">
  <strong>Automated retinal image quality gating for the Wisconsin Reading Center</strong>
</p>

<p align="center">
  <a href="https://www.ophth.wisc.edu/research/wrc/">Wisconsin Reading Center</a> &middot;
  <a href="#mcp-tools">8 MCP Tools</a> &middot;
  <a href="#quick-start">Quick Start</a> &middot;
  <a href="#deploy">Deploy</a>
</p>

---

## Try it

The deployed home page has a live demo: pick one of seven sample images (good, soft, blurry, dark, color cast, low
resolution, corrupted) or drop in your own photo (JPEG or PNG, up to 4 MB) and see the verdict and every check.
Uploads are analyzed in memory and not stored. The samples are variations of one public-domain fundus photograph
(CC0, Mikael Häggström, Wikimedia Commons).

Run it locally with `make demo` and open http://127.0.0.1:8001.

The web demo accepts uploads. The **MCP tools still take a public image URL**.

## Impact

The Wisconsin Reading Center (UW-Madison, Dept of Ophthalmology & Visual Sciences) grades **~100,000 retinal images per year** across multi-center clinical trials. Every image must meet quality standards before a human grader can assess it for disease markers like diabetic retinopathy, macular degeneration, and glaucoma.

**The problem:** Bad images waste grader time, delay trial results, and force expensive patient retakes.

| Metric | Value |
|---|---|
| Images reviewed per year | ~100,000 |
| Typical ungradable rate | ~5% |
| Wasted review cycles per year | ~5,000 |
| Time per wasted cycle (grade + flag + retake) | ~30 min |
| **Technician hours lost per year** | **~2,500** |
| Cost of this agent | $20/month Vercel plan |

**This agent catches bad images in seconds at upload, before a human ever sees them.**

---

## Architecture

```
                                 DATA QUALITY AGENT
                                 ==================

  MCP Client                         Vercel Serverless
  ----------------------             ----------------------------------
  | OpenCode           |             |  Python + FastMCP + Pydantic   |
  | Claude Desktop     |   POST      |                                |
  | Any MCP client     | ---------> |  /mcp  (Streamable HTTP)       |
  ----------------------             |    |                            |
                                     |    +-- check_image_quality     |
          image_url                  |    +-- check_sharpness         |
      (public URL) -->               |    +-- check_resolution        |
                                     |    +-- check_format            |
          <-- QualityReport          |    +-- check_illumination      |
          ACCEPT / REVIEW / REJECT   |    +-- check_color             |
                                     |    +-- validate_metadata       |
                                     |    +-- assess_fundus_quality   |
                                     |         (EyeQ deep learning)   |
                                     ----------------------------------
```

---

## MCP Tools

All tools accept `image_url` (string) — a publicly accessible image URL.

| Tool | What it does | Returns |
|---|---|---|
| `tool_check_image_quality` | **Primary tool.** Runs all checks, returns combined verdict | `ACCEPT` / `REVIEW` / `REJECT` + full report |
| `tool_check_sharpness` | Blur detection: brightness-normalized Laplacian variance inside the retina | Score, pass/fail, detail |
| `tool_check_resolution` | Dimension validation (default min 1024x1024) | Width, height, megapixels, pass/fail |
| `tool_check_format` | File format (magic bytes) + corruption detection | Format name, valid, corrupted |
| `tool_check_illumination` | Brightness, uniformity, vignetting | Mean/std brightness, uniformity, vignetting flag |
| `tool_check_color` | RGB color space + channel balance | Mode, channels, balanced, channel means |
| `tool_validate_metadata` | EXIF extraction | Has EXIF, field key-value pairs |
| `tool_assess_fundus_quality` | EyeQ/MCF-Net deep learning (DenseNet121) | Good / Usable / Reject + confidence |

---

## Quick Start

```bash
# Install
make dev

# Run the MCP server locally (MCP endpoint only)
make serve
# -> http://127.0.0.1:8000/mcp

# Run the web demo + docs page locally (upload an image, see the verdict)
make demo
# -> http://127.0.0.1:8001

# Run tests
make test

# Remove Python artifacts (__pycache__, .pyc, etc.)
make clean
```

### Test with curl

```bash
# 1. Initialize MCP session (grab Mcp-Session-Id from response headers)
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{
    "protocolVersion":"2025-03-26","capabilities":{},
    "clientInfo":{"name":"test","version":"0.1"}}}' \
  -i

# 2. List tools
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

# 3. Full quality check
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{
    "name":"tool_check_image_quality",
    "arguments":{"image_url":"https://picsum.photos/2048/2048.jpg"}}}'
```

---

## Connect Your Agent

### OpenCode

```json
{
  "mcp": {
    "data-quality": {
      "type": "remote",
      "url": "https://YOUR_DEPLOYMENT_URL/mcp",
      "enabled": true
    }
  }
}
```

### Claude Desktop

```json
{
  "mcpServers": {
    "data-quality": {
      "url": "https://YOUR_DEPLOYMENT_URL/mcp"
    }
  }
}
```

---

## Configuration

All quality thresholds are configurable via environment variables (or `QualityConfig` Pydantic model):

| Variable | Default | Description |
|---|---|---|
| `QUALITY_SHARPNESS_PASS` | `3.5` | Sharpness score to pass (normalized, see note below) |
| `QUALITY_SHARPNESS_REVIEW` | `1.5` | Below this is a clear blur (reject); between the two is review |
| `QUALITY_MIN_WIDTH` | `1024` | Minimum image width (px) |
| `QUALITY_MIN_HEIGHT` | `1024` | Minimum image height (px) |
| `QUALITY_BRIGHTNESS_MIN_PASS` | `60` | Min brightness to pass |
| `QUALITY_BRIGHTNESS_MAX_PASS` | `200` | Max brightness to pass |
| `QUALITY_VIGNETTING_RATIO_MIN` | `0.6` | Outer/center retina brightness below this is flagged |
| `QUALITY_COLOR_GR_MIN` / `_MAX` | `0.25` / `0.85` | Allowed retina green/red ratio (healthy fundus is red-orange) |
| `QUALITY_COLOR_BR_MAX` | `0.7` | Max blue/red ratio (higher is a blue cast) |
| `QUALITY_ALLOWED_FORMATS` | `JPEG,PNG,TIFF,BMP` | Accepted file formats |
| `QUALITY_EYEQ_ENABLED` | `true` | Enable/disable EyeQ DL model |

**Calibration note.** The checks measure the retina disc only (the black border of a fundus photo is ignored), and the
defaults above were tuned on one real photograph plus degraded copies of it. They are a starting point: tune them on
real reading-center images before relying on the verdicts clinically.

```bash
# Example: run without deep learning model
QUALITY_EYEQ_ENABLED=false make serve
```

---

## Deploy

```bash
make deploy    # vercel --prod
```

EyeQ deep learning runs locally only (PyTorch too large for Vercel lambda). On Vercel, classical checks run and the report notes that EyeQ was not available (it does not count toward the verdict).

`requirements.txt` pins `mcp<2`: the MCP SDK 2.x renamed `FastMCP`, which this server uses. Lift the pin only after migrating.

---

## Tech Stack

- **Python** + **Pydantic** (typed models for all inputs/outputs/config)
- **FastMCP** (MCP server SDK, Streamable HTTP transport)
- **OpenCV** headless + **Pillow** (classical image quality checks)
- **PyTorch** + **EyeQ/MCF-Net** (fundus quality deep learning, local only)
- **Vercel** serverless deployment

## Makefile Commands

| Command | What it does |
|---|---|
| `make install` | Create venv + install deps + PyTorch CPU |
| `make dev` | Install with dev deps (pytest, ruff, mypy) |
| `make test` | Run all tests |
| `make lint` | Ruff + mypy |
| `make serve` | Start MCP server at localhost:8000 |
| `make clean` | Remove all `__pycache__` / `.pyc` artifacts |
| `make deploy` | Deploy to Vercel |
| `make fetch-model` | Download EyeQ model weights |

## License

EyeQ model weights are CC BY-NC-SA 4.0 (non-commercial use only).

---

<p align="center">
  Built for the <a href="https://www.ophth.wisc.edu/research/wrc/">Wisconsin Reading Center</a>
  &middot; UW-Madison Dept of Ophthalmology &amp; Visual Sciences
</p>
