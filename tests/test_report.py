"""Verdict logic and the demo sample images (derived from one real, public-domain fundus photo)."""

import io

import pytest
from PIL import Image

from src.models import Verdict
from src.report import run_quality_checks, unreadable_report
from src.samples import SAMPLES, make_sample


def _report(name: str):
    raw = make_sample(name)
    image = Image.open(io.BytesIO(raw))
    image.load()
    return run_quality_checks(image, raw, name)


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: s.name)
def test_sample_gets_expected_verdict(sample):
    if sample.name == "corrupted":
        report = unreadable_report("corrupted.jpg", "truncated")
    else:
        report = _report(sample.name)
    assert report.verdict == Verdict(sample.expected)


def test_real_fundus_photo_is_accepted():
    """Regression: the original whole-frame checks called a normal real fundus photo blurry and mis-colored."""
    report = _report("good")
    assert report.verdict == Verdict.ACCEPT
    assert all(c.passed for c in report.checks if c.name != "metadata")


def test_borderline_focus_is_review_not_reject():
    assert _report("soft").verdict == Verdict.REVIEW


def test_heavy_blur_is_reject():
    report = _report("blurry")
    assert report.verdict == Verdict.REJECT
    assert "sharpness" in report.summary


def test_missing_exif_alone_does_not_change_verdict():
    report = _report("good")
    meta = next(c for c in report.checks if c.name == "metadata")
    assert not meta.passed
    assert report.verdict == Verdict.ACCEPT


def test_unavailable_eyeq_is_noted_not_counted():
    report = _report("good")
    assert report.fundus_assessment is None
    assert not any(c.name == "fundus_quality" for c in report.checks)
    assert any("EyeQ" in n for n in report.notes)


def test_unreadable_report_is_reject():
    report = unreadable_report("x.jpg", "not an image")
    assert report.verdict == Verdict.REJECT
    assert report.checks[0].name == "format"
