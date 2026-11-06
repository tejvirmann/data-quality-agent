"""Run every quality check on one image and combine them into a verdict.

Shared by the MCP tool (tool_check_image_quality) and the web demo (/api/check), so both always agree.
"""

import logging

from PIL import Image

from src.checks.color import check_color
from src.checks.format_check import check_format
from src.checks.illumination import check_illumination
from src.checks.metadata import validate_metadata
from src.checks.resolution import check_resolution
from src.checks.sharpness import check_sharpness
from src.config import config
from src.models import CheckResult, FundusAssessment, QualityReport, Verdict

logger = logging.getLogger(__name__)

CRITICAL_CHECKS = {"format", "sharpness", "fundus_quality"}

_HEADLINES = {
    Verdict.ACCEPT: "Ready for clinical grading.",
    Verdict.REVIEW: "Minor issues: a person should look at this before grading.",
    Verdict.REJECT: "Not gradable: request a retake.",
}


def _is_critical(check: CheckResult) -> bool:
    """A failure that forces REJECT. Borderline focus is only a REVIEW; clearly blurry is a REJECT."""
    if check.name == "sharpness":
        return float(check.metrics.get("score", 0)) < config.sharpness_review
    return check.name in CRITICAL_CHECKS


def run_quality_checks(image: Image.Image, raw_bytes: bytes, source: str) -> QualityReport:
    """Run all classical checks (and EyeQ when it is installed) and return the full report."""
    sharpness = check_sharpness(image)
    resolution = check_resolution(image)
    fmt = check_format(image, raw_bytes)
    illumination = check_illumination(image)
    color = check_color(image)
    metadata = validate_metadata(image)

    checks = [
        CheckResult(name="sharpness", passed=sharpness.is_sharp, detail=sharpness.detail,
                    metrics={"score": sharpness.score, "pass_at": config.sharpness_pass,
                             "review_at": config.sharpness_review}),
        CheckResult(name="resolution", passed=resolution.meets_minimum,
                    detail=(f"{resolution.width}x{resolution.height} ({resolution.megapixels} MP), "
                            f"minimum {config.min_width}x{config.min_height}"),
                    metrics={"width": resolution.width, "height": resolution.height,
                             "megapixels": resolution.megapixels}),
        CheckResult(name="format", passed=fmt.valid and not fmt.corrupted, detail=fmt.detail,
                    metrics={"format": fmt.format, "corrupted": fmt.corrupted}),
        CheckResult(name="illumination", passed=illumination.uniform, detail=illumination.detail,
                    metrics={"mean_brightness": illumination.mean_brightness, "std": illumination.std_brightness,
                             "vignetting": illumination.vignetting_detected}),
        CheckResult(name="color", passed=color.balanced, detail=color.detail,
                    metrics={"mode": color.mode, "rgb_means": color.channel_means}),
        CheckResult(name="metadata", passed=metadata.has_exif,
                    detail=(f"{len(metadata.fields)} EXIF fields found" if metadata.has_exif
                            else "No EXIF data (informational)"),
                    metrics={"exif_fields": len(metadata.fields)}),
    ]

    fundus: FundusAssessment | None = None
    notes: list[str] = []
    if config.eyeq_enabled:
        try:
            from src.ml.eyeq import assess_fundus_quality

            fundus = assess_fundus_quality(image)
            checks.append(CheckResult(
                name="fundus_quality", passed=fundus.grade.value != "reject",
                detail=f"EyeQ grade: {fundus.grade.value} (confidence {fundus.confidence})",
                metrics={"grade": fundus.grade.value, "confidence": fundus.confidence},
            ))
        except Exception as e:  # torch or weights not installed (the Vercel deploy): report it, don't count it
            logger.info("EyeQ assessment unavailable: %s", e)
            notes.append("Deep-learning grade (EyeQ) is not available on this deployment; "
                         "the classical checks above were run.")

    # Missing EXIF is informational, so it never counts toward the verdict.
    failed = [c for c in checks if not c.passed and c.name != "metadata"]
    if any(_is_critical(c) for c in failed) or len(failed) >= 3:
        verdict = Verdict.REJECT
    elif failed:
        verdict = Verdict.REVIEW
    else:
        verdict = Verdict.ACCEPT

    summary = _HEADLINES[verdict]
    if failed:
        summary += " Failed: " + ", ".join(c.name for c in failed) + "."
    return QualityReport(verdict=verdict, checks=checks, fundus_assessment=fundus, image_url=source,
                         summary=summary, notes=notes)


def unreadable_report(source: str, reason: str) -> QualityReport:
    """Report for a file that cannot be decoded at all (truncated, not an image, wrong format)."""
    check = CheckResult(name="format", passed=False, detail=f"File could not be read as an image: {reason}",
                        metrics={"corrupted": True})
    return QualityReport(verdict=Verdict.REJECT, checks=[check], image_url=source,
                         summary=_HEADLINES[Verdict.REJECT] + " Failed: format.")
