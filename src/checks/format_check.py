"""File format validation and corruption detection."""

import io

from PIL import Image

from src.config import config
from src.models import FormatResult


def check_format(image: Image.Image, raw_bytes: bytes) -> FormatResult:
    """Validate image format and check for corruption.

    Uses PIL to verify header integrity and attempts full pixel load
    to catch truncated/corrupted files.
    """
    detected_format = image.format or "UNKNOWN"
    valid = detected_format.upper() in [f.upper() for f in config.allowed_formats]

    # Check for corruption by attempting full pixel load
    corrupted = False
    detail = ""
    try:
        verify_image = Image.open(io.BytesIO(raw_bytes))
        verify_image.verify()

        reload_image = Image.open(io.BytesIO(raw_bytes))
        reload_image.load()
    except Exception as e:
        corrupted = True
        detail = f"Corruption detected: {e}"

    if not detail:
        if valid:
            detail = f"Valid {detected_format} format"
        else:
            detail = (
                f"Format {detected_format} not in allowed list: "
                f"{', '.join(config.allowed_formats)}"
            )

    return FormatResult(
        format=detected_format,
        valid=valid,
        corrupted=corrupted,
        detail=detail,
    )
