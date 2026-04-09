"""Unit tests for all classical quality checks."""

from PIL import Image

from src.checks.color import check_color
from src.checks.format_check import check_format
from src.checks.illumination import check_illumination
from src.checks.metadata import validate_metadata
from src.checks.resolution import check_resolution
from src.checks.sharpness import check_sharpness


class TestSharpness:
    def test_sharp_image(self, good_image: Image.Image):
        result = check_sharpness(good_image)
        assert result.score > 0
        # Random noise image should have decent variance
        assert result.is_sharp or result.score > 50

    def test_blurry_image(self, blurry_image: Image.Image):
        result = check_sharpness(blurry_image)
        assert not result.is_sharp
        assert result.score < 80


class TestResolution:
    def test_good_resolution(self, good_image: Image.Image):
        result = check_resolution(good_image)
        assert result.width == 2048
        assert result.height == 2048
        assert result.meets_minimum
        assert result.megapixels == 4.19

    def test_small_resolution(self, small_image: Image.Image):
        result = check_resolution(small_image)
        assert result.width == 256
        assert result.height == 256
        assert not result.meets_minimum


class TestFormat:
    def test_valid_jpeg(self, good_image_bytes: tuple[Image.Image, bytes]):
        image, raw = good_image_bytes
        result = check_format(image, raw)
        assert result.format == "JPEG"
        assert result.valid
        assert not result.corrupted

    def test_valid_png(self, png_image_bytes: tuple[Image.Image, bytes]):
        image, raw = png_image_bytes
        result = check_format(image, raw)
        assert result.format == "PNG"
        assert result.valid
        assert not result.corrupted

    def test_corrupted_bytes(self, good_image_bytes: tuple[Image.Image, bytes]):
        image, raw = good_image_bytes
        # Truncate bytes to simulate corruption
        corrupted_raw = raw[:100]
        result = check_format(image, corrupted_raw)
        assert result.corrupted


class TestIllumination:
    def test_normal_illumination(self, good_image: Image.Image):
        result = check_illumination(good_image)
        assert 40 < result.mean_brightness < 230

    def test_dark_image(self, dark_image: Image.Image):
        result = check_illumination(dark_image)
        assert result.mean_brightness < 40
        assert "Underexposed" in result.detail

    def test_bright_image(self, bright_image: Image.Image):
        result = check_illumination(bright_image)
        assert result.mean_brightness > 200
        assert "Overexposed" in result.detail


class TestColor:
    def test_balanced_image(self, good_image: Image.Image):
        result = check_color(good_image)
        assert result.mode == "RGB"
        assert result.channels == 3

    def test_tinted_image(self, tinted_image: Image.Image):
        result = check_color(tinted_image)
        assert not result.balanced
        assert "imbalance" in result.detail.lower()


class TestMetadata:
    def test_no_exif(self, good_image: Image.Image):
        result = validate_metadata(good_image)
        # Synthetic images have no EXIF
        assert not result.has_exif
        assert result.fields == {}
