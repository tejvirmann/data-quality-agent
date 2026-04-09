"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from src.models import (
    CheckResult,
    ColorResult,
    FormatResult,
    FundusAssessment,
    FundusGrade,
    IlluminationResult,
    ImageInput,
    MetadataResult,
    QualityReport,
    ResolutionResult,
    SharpnessResult,
    Verdict,
)


class TestImageInput:
    def test_valid_url(self):
        inp = ImageInput(image_url="https://example.com/image.jpg")
        assert str(inp.image_url) == "https://example.com/image.jpg"

    def test_invalid_url(self):
        with pytest.raises(ValidationError):
            ImageInput(image_url="not-a-url")


class TestSharpnessResult:
    def test_creation(self):
        r = SharpnessResult(score=155.3, is_sharp=True, detail="Sharp")
        assert r.score == 155.3
        assert r.is_sharp


class TestResolutionResult:
    def test_creation(self):
        r = ResolutionResult(width=2048, height=2048, meets_minimum=True, megapixels=4.19)
        assert r.megapixels == 4.19


class TestQualityReport:
    def test_full_report(self):
        report = QualityReport(
            verdict=Verdict.ACCEPT,
            checks=[
                CheckResult(name="sharpness", passed=True, detail="OK"),
                CheckResult(name="resolution", passed=True, detail="2048x2048"),
            ],
            fundus_assessment=FundusAssessment(
                grade=FundusGrade.GOOD,
                confidence=0.95,
                probabilities={"good": 0.95, "usable": 0.04, "reject": 0.01},
            ),
            image_url="https://example.com/fundus.jpg",
        )
        assert report.verdict == Verdict.ACCEPT
        assert len(report.checks) == 2
        assert report.fundus_assessment is not None
        assert report.fundus_assessment.grade == FundusGrade.GOOD

    def test_report_without_fundus(self):
        report = QualityReport(
            verdict=Verdict.REVIEW,
            checks=[CheckResult(name="sharpness", passed=False, detail="Blurry")],
            image_url="https://example.com/blurry.jpg",
        )
        assert report.fundus_assessment is None


class TestVerdictEnum:
    def test_values(self):
        assert Verdict.ACCEPT.value == "accept"
        assert Verdict.REVIEW.value == "review"
        assert Verdict.REJECT.value == "reject"


class TestFundusGrade:
    def test_values(self):
        assert FundusGrade.GOOD.value == "good"
        assert FundusGrade.USABLE.value == "usable"
        assert FundusGrade.REJECT.value == "reject"
