"""Fetch images from URLs for quality checking."""

import io

import httpx
from PIL import Image


async def load_image_from_url(url: str) -> tuple[Image.Image, bytes]:
    """Fetch an image from a URL and return both PIL Image and raw bytes.

    Returns:
        Tuple of (PIL Image, raw bytes).

    Raises:
        httpx.HTTPStatusError: If the URL returns a non-2xx status.
        PIL.UnidentifiedImageError: If the content isn't a valid image.
    """
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(str(url))
        response.raise_for_status()

    raw_bytes = response.content
    image = Image.open(io.BytesIO(raw_bytes))
    return image, raw_bytes
