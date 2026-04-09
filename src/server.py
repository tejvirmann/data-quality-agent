"""FastMCP server with all quality check tools."""

import logging

from mcp.server.fastmcp import FastMCP

from src.checks.color import check_color
from src.checks.format_check import check_format
from src.checks.illumination import check_illumination
from src.checks.metadata import validate_metadata
from src.checks.resolution import check_resolution
from src.checks.sharpness import check_sharpness
from src.config import config
from src.image_loader import load_image_from_url
from src.models import (
    CheckResult,
    ColorResult,
    FormatResult,
    FundusAssessment,
    IlluminationResult,
    MetadataResult,
    QualityReport,
    ResolutionResult,
    SharpnessResult,
    Verdict,
)

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Data Quality Agent",
    description="Automated image quality assessment for the Wisconsin Reading Center. "
    "Checks fundus/retinal images for sharpness, resolution, format, illumination, "
    "color balance, metadata, and runs EyeQ deep learning grading.",
)


# --- Individual Tools ---


@mcp.tool()
async def tool_check_sharpness(image_url: str) -> SharpnessResult:
    """Check if an image is blurry using Laplacian variance. Higher score = sharper."""
    image, _ = await load_image_from_url(image_url)
    return check_sharpness(image)


@mcp.tool()
async def tool_check_resolution(image_url: str) -> ResolutionResult:
    """Validate image dimensions against minimum requirements (default 1024x1024)."""
    image, _ = await load_image_from_url(image_url)
    return check_resolution(image)


@mcp.tool()
async def tool_check_format(image_url: str) -> FormatResult:
    """Validate image file format and check for corruption."""
    image, raw_bytes = await load_image_from_url(image_url)
    return check_format(image, raw_bytes)


@mcp.tool()
async def tool_check_illumination(image_url: str) -> IlluminationResult:
    """Analyze image brightness, uniformity, and detect vignetting."""
    image, _ = await load_image_from_url(image_url)
    return check_illumination(image)


@mcp.tool()
async def tool_check_color(image_url: str) -> ColorResult:
    """Validate color space (should be RGB) and check channel balance."""
    image, _ = await load_image_from_url(image_url)
    return check_color(image)


@mcp.tool()
async def tool_validate_metadata(image_url: str) -> MetadataResult:
    """Extract and validate EXIF metadata from the image."""
    image, _ = await load_image_from_url(image_url)
    return validate_metadata(image)


@mcp.tool()
async def tool_assess_fundus_quality(image_url: str) -> FundusAssessment:
    """Run EyeQ/MCF-Net deep learning model for fundus-specific quality grading.

    Returns Good / Usable / Reject with confidence scores.
    Requires model weights (run 'make fetch-model' first).
    """
    from src.ml.eyeq import assess_fundus_quality

    image, _ = await load_image_from_url(image_url)
    return assess_fundus_quality(image)


# --- Orchestrator ---


@mcp.tool()
async def tool_check_image_quality(image_url: str) -> QualityReport:
    """Run ALL quality checks on an image and return a full report with verdict.

    Verdict is ACCEPT, REVIEW, or REJECT based on combined check results.
    Includes classical checks (sharpness, resolution, format, illumination, color,
    metadata) and optionally EyeQ deep learning fundus grading.
    """
    image, raw_bytes = await load_image_from_url(image_url)

    # Run all classical checks
    sharpness = check_sharpness(image)
    resolution = check_resolution(image)
    fmt = check_format(image, raw_bytes)
    illumination = check_illumination(image)
    color = check_color(image)
    metadata = validate_metadata(image)

    checks: list[CheckResult] = [
        CheckResult(name="sharpness", passed=sharpness.is_sharp, detail=sharpness.detail),
        CheckResult(name="resolution", passed=resolution.meets_minimum, detail=f"{resolution.width}x{resolution.height}, {resolution.megapixels}MP"),
        CheckResult(name="format", passed=fmt.valid and not fmt.corrupted, detail=fmt.detail),
        CheckResult(name="illumination", passed=illumination.uniform, detail=illumination.detail),
        CheckResult(name="color", passed=color.balanced, detail=color.detail),
        CheckResult(name="metadata", passed=metadata.has_exif, detail=f"{len(metadata.fields)} EXIF fields found" if metadata.has_exif else "No EXIF data"),
    ]

    # Try EyeQ if enabled
    fundus_assessment: FundusAssessment | None = None
    if config.eyeq_enabled:
        try:
            from src.ml.eyeq import assess_fundus_quality
            fundus_assessment = assess_fundus_quality(image)
            checks.append(
                CheckResult(
                    name="fundus_quality",
                    passed=fundus_assessment.grade.value != "reject",
                    detail=f"EyeQ grade: {fundus_assessment.grade.value} (confidence: {fundus_assessment.confidence})",
                )
            )
        except Exception as e:
            logger.warning("EyeQ assessment skipped: %s", e)
            checks.append(
                CheckResult(name="fundus_quality", passed=True, detail=f"Skipped: {e}")
            )

    # Determine verdict
    failed = [c for c in checks if not c.passed]
    critical_failures = {"format", "sharpness", "fundus_quality"}
    has_critical_failure = any(c.name in critical_failures for c in failed)

    if has_critical_failure or len(failed) >= 3:
        verdict = Verdict.REJECT
    elif len(failed) >= 1:
        verdict = Verdict.REVIEW
    else:
        verdict = Verdict.ACCEPT

    return QualityReport(
        verdict=verdict,
        checks=checks,
        fundus_assessment=fundus_assessment,
        image_url=str(image_url),
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
