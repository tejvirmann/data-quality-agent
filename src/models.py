"""Pydantic models for all inputs, outputs, and quality assessments."""

from enum import Enum

from pydantic import BaseModel, HttpUrl


class Verdict(str, Enum):
    """Overall quality verdict for an image."""

    ACCEPT = "accept"
    REVIEW = "review"
    REJECT = "reject"


class FundusGrade(str, Enum):
    """EyeQ deep learning quality grade for fundus images."""

    GOOD = "good"
    USABLE = "usable"
    REJECT = "reject"


# --- Tool Inputs ---


class ImageInput(BaseModel):
    """Input for all quality check tools."""

    image_url: HttpUrl


# --- Individual Check Results ---


class SharpnessResult(BaseModel):
    """Result of blur/sharpness detection."""

    score: float
    is_sharp: bool
    detail: str


class ResolutionResult(BaseModel):
    """Result of resolution validation."""

    width: int
    height: int
    meets_minimum: bool
    megapixels: float


class FormatResult(BaseModel):
    """Result of format and corruption checks."""

    format: str
    valid: bool
    corrupted: bool
    detail: str


class IlluminationResult(BaseModel):
    """Result of illumination/brightness analysis."""

    mean_brightness: float
    std_brightness: float
    uniform: bool
    vignetting_detected: bool
    detail: str


class ColorResult(BaseModel):
    """Result of color space validation."""

    mode: str
    channels: int
    balanced: bool
    channel_means: list[float]
    detail: str


class MetadataResult(BaseModel):
    """Result of EXIF metadata extraction."""

    has_exif: bool
    fields: dict[str, str]


# --- Deep Learning ---


class FundusAssessment(BaseModel):
    """EyeQ/MCF-Net deep learning quality assessment."""

    grade: FundusGrade
    confidence: float
    probabilities: dict[str, float]


# --- Orchestrator Output ---


class CheckResult(BaseModel):
    """Summary of a single quality check within the orchestrator report."""

    name: str
    passed: bool
    detail: str


class QualityReport(BaseModel):
    """Full quality report from the orchestrator tool."""

    verdict: Verdict
    checks: list[CheckResult]
    fundus_assessment: FundusAssessment | None = None
    image_url: str
