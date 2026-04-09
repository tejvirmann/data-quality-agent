"""Shared test fixtures."""

import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _make_image(width: int, height: int, color: tuple[int, ...] = (128, 128, 128), mode: str = "RGB") -> Image.Image:
    """Create a solid-color test image."""
    return Image.new(mode, (width, height), color)


def _image_to_bytes(image: Image.Image, fmt: str = "JPEG") -> bytes:
    """Convert PIL Image to raw bytes."""
    buf = io.BytesIO()
    image.save(buf, format=fmt)
    buf.seek(0)
    # Re-open to set .format attribute
    reopened = Image.open(buf)
    reopened.load()
    return buf.getvalue()


@pytest.fixture
def good_image() -> Image.Image:
    """A 2048x2048 RGB image with varied content (not blurry)."""
    rng = np.random.RandomState(42)
    arr = rng.randint(80, 200, (2048, 2048, 3), dtype=np.uint8)
    # Add some high-frequency detail for sharpness
    for i in range(0, 2048, 4):
        arr[i, :, :] = arr[i, :, :] // 2
    return Image.fromarray(arr, "RGB")


@pytest.fixture
def blurry_image() -> Image.Image:
    """A uniform low-variance image (will score low on Laplacian)."""
    arr = np.full((1024, 1024, 3), 128, dtype=np.uint8)
    # Add minimal noise
    rng = np.random.RandomState(0)
    arr = arr + rng.randint(-2, 3, arr.shape, dtype=np.int8)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


@pytest.fixture
def small_image() -> Image.Image:
    """A 256x256 image (below resolution minimum)."""
    return _make_image(256, 256)


@pytest.fixture
def dark_image() -> Image.Image:
    """A very dark image (underexposed)."""
    return _make_image(1024, 1024, color=(15, 15, 15))


@pytest.fixture
def bright_image() -> Image.Image:
    """A very bright image (overexposed)."""
    return _make_image(1024, 1024, color=(245, 245, 245))


@pytest.fixture
def tinted_image() -> Image.Image:
    """An image with extreme red tint (color imbalance)."""
    return _make_image(1024, 1024, color=(220, 50, 50))


@pytest.fixture
def good_image_bytes(good_image: Image.Image) -> tuple[Image.Image, bytes]:
    """Good image with raw JPEG bytes."""
    raw = _image_to_bytes(good_image, "JPEG")
    img = Image.open(io.BytesIO(raw))
    return img, raw


@pytest.fixture
def png_image_bytes() -> tuple[Image.Image, bytes]:
    """PNG image with raw bytes."""
    img = _make_image(1024, 1024)
    raw = _image_to_bytes(img, "PNG")
    img = Image.open(io.BytesIO(raw))
    return img, raw
