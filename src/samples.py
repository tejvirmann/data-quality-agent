"""Demo sample images, derived on the fly from one real, public-domain fundus photograph.

Source: "Fundus photograph of normal left eye" by Mikael Häggström, Wikimedia Commons, CC0 (public domain).
The degraded variants are made with Pillow so each demonstrates one failure the checks should catch.
"""

import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

_SOURCE = Path(__file__).parent / "samples" / "normal_fundus.jpg"


@dataclass(frozen=True)
class Sample:
    name: str
    title: str
    blurb: str
    expected: str  # the verdict the checks should give


SAMPLES: list[Sample] = [
    Sample("good", "Good image", "A normal retina, in focus and evenly lit.", "accept"),
    Sample("soft", "Slightly soft", "Mild defocus: borderline sharpness.", "review"),
    Sample("blurry", "Blurry", "Heavy blur: the vessels cannot be graded.", "reject"),
    Sample("dark", "Underexposed", "Too dark to see retinal detail.", "review"),
    Sample("bluecast", "Color cast", "Wrong color profile, a camera or processing fault.", "review"),
    Sample("lowres", "Low resolution", "Too few pixels for reliable grading.", "review"),
    Sample("corrupted", "Corrupted file", "A truncated upload that will not decode.", "reject"),
]
_BY_NAME = {s.name: s for s in SAMPLES}


def _jpeg(image: Image.Image, quality: int = 92) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def make_sample(name: str) -> bytes:
    """JPEG bytes for a named sample. Raises KeyError for an unknown name."""
    if name not in _BY_NAME:
        raise KeyError(name)
    base = Image.open(_SOURCE).convert("RGB")
    arr = np.array(base)

    if name == "good":
        return _SOURCE.read_bytes()
    if name == "soft":
        return _jpeg(base.filter(ImageFilter.GaussianBlur(2)))
    if name == "blurry":
        return _jpeg(base.filter(ImageFilter.GaussianBlur(8)))
    if name == "dark":
        return _jpeg(Image.fromarray((arr * 0.35).astype(np.uint8)))
    if name == "bluecast":
        return _jpeg(Image.fromarray(arr[:, :, ::-1].copy()))
    if name == "lowres":
        return _jpeg(base.resize((640, 640), Image.LANCZOS))
    # corrupted: cut the file off partway through
    data = _SOURCE.read_bytes()
    return data[: int(len(data) * 0.55)]
