"""Image resolution validation."""

from PIL import Image

from src.config import config
from src.models import ResolutionResult


def check_resolution(image: Image.Image) -> ResolutionResult:
    """Validate image dimensions against minimum requirements."""
    width, height = image.size
    megapixels = round((width * height) / 1_000_000, 2)
    meets_minimum = width >= config.min_width and height >= config.min_height

    return ResolutionResult(
        width=width,
        height=height,
        meets_minimum=meets_minimum,
        megapixels=megapixels,
    )
