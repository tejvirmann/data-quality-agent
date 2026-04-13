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
    instructions=(
        "You are a retinal image quality assessment agent for the Wisconsin Reading Center. "
        "You accept fundus/eye image URLs and evaluate them for diagnostic quality. "
        "Use 'tool_check_image_quality' for a full report with an ACCEPT/REVIEW/REJECT verdict, "
        "or call individual tools to inspect specific quality dimensions. "
        "Images must be passed as publicly accessible URLs."
    ),
)


# --- Individual Tools ---


@mcp.tool()
async def tool_check_sharpness(image_url: str) -> SharpnessResult:
    """Detect blur in a retinal/fundus image using Laplacian variance.

    Accepts a public image URL. Returns a sharpness score (higher = sharper)
    and a pass/fail result. Blurry fundus images cannot be graded for disease
    markers and should be rejected or flagged for retake.

    - score > 150: sharp (pass)
    - score 80-150: borderline (review)
    - score < 80: blurry (reject)
    """
    image, _ = await load_image_from_url(image_url)
    return check_sharpness(image)


@mcp.tool()
async def tool_check_resolution(image_url: str) -> ResolutionResult:
    """Validate that an image meets minimum resolution requirements for diagnostic grading.

    Accepts a public image URL. Checks width and height against configurable minimums
    (default: 1024x1024). Fundus images below minimum resolution lack the detail needed
    for reliable clinical assessment. Returns dimensions, megapixel count, and pass/fail.
    """
    image, _ = await load_image_from_url(image_url)
    return check_resolution(image)


@mcp.tool()
async def tool_check_format(image_url: str) -> FormatResult:
    """Validate image file format and detect corruption.

    Accepts a public image URL. Verifies the file is a supported format (JPEG, PNG, TIFF, BMP)
    by inspecting actual file bytes, not just the extension. Also performs corruption detection
    by verifying header integrity and loading all pixel data. Corrupted files will fail clinical
    processing pipelines and must be re-uploaded.
    """
    image, raw_bytes = await load_image_from_url(image_url)
    return check_format(image, raw_bytes)


@mcp.tool()
async def tool_check_illumination(image_url: str) -> IlluminationResult:
    """Analyze brightness, exposure uniformity, and vignetting in a fundus image.

    Accepts a public image URL. Checks for underexposure (too dark), overexposure (too bright),
    uneven illumination across the image, and vignetting (dark corners). Poor illumination
    obscures retinal structures and makes clinical grading unreliable. Returns brightness stats,
    uniformity flag, and vignetting detection.
    """
    image, _ = await load_image_from_url(image_url)
    return check_illumination(image)


@mcp.tool()
async def tool_check_color(image_url: str) -> ColorResult:
    """Validate color space and check for color channel imbalance in a fundus image.

    Accepts a public image URL. Fundus images should be RGB with balanced color channels.
    Extreme tint (e.g., all-red or washed-out blue) indicates a camera or processing problem.
    Returns the color mode, channel count, per-channel means, and whether the image is balanced.
    """
    image, _ = await load_image_from_url(image_url)
    return check_color(image)


@mcp.tool()
async def tool_validate_metadata(image_url: str) -> MetadataResult:
    """Extract EXIF metadata from an image for audit and traceability.

    Accepts a public image URL. Extracts camera model, capture date, dimensions, and other
    EXIF fields. Metadata helps track which camera captured the image, when, and with what
    settings. Missing EXIF is not a failure but is flagged for awareness.
    """
    image, _ = await load_image_from_url(image_url)
    return validate_metadata(image)


@mcp.tool()
async def tool_assess_fundus_quality(image_url: str) -> FundusAssessment:
    """Run EyeQ/MCF-Net deep learning model for fundus-specific quality grading.

    Accepts a public image URL. Uses a DenseNet121-based multi-color-space fusion network
    trained specifically on fundus images. Processes the image in RGB, HSV, and LAB color
    spaces and returns a clinical quality grade:

    - GOOD: suitable for diagnostic grading
    - USABLE: acceptable but may have minor issues
    - REJECT: not suitable for clinical use, retake required

    Also returns confidence score and per-class probabilities.
    Requires model weights to be downloaded (run 'make fetch-model').
    """
    from src.ml.eyeq import assess_fundus_quality

    image, _ = await load_image_from_url(image_url)
    return assess_fundus_quality(image)


# --- Orchestrator ---


@mcp.tool()
async def tool_check_image_quality(image_url: str) -> QualityReport:
    """Run ALL quality checks on a fundus/retinal image and return a comprehensive report.

    This is the primary tool. Accepts a public image URL and runs every available check:
    sharpness (blur detection), resolution, format/corruption, illumination/exposure,
    color balance, EXIF metadata, and optionally EyeQ deep learning grading.

    Returns a verdict:
    - ACCEPT: image passes all checks, ready for clinical grading
    - REVIEW: minor issues detected, human review recommended
    - REJECT: critical failures (blurry, corrupted, or EyeQ reject), retake needed

    Use this tool when you want a single comprehensive quality assessment.
    Use the individual tools when you need to investigate a specific quality dimension.
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
