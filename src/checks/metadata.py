"""EXIF metadata extraction and validation."""

from PIL import Image
from PIL.ExifTags import TAGS

from src.models import MetadataResult


def validate_metadata(image: Image.Image) -> MetadataResult:
    """Extract and validate EXIF metadata from the image."""
    exif_data = image.getexif()

    if not exif_data:
        return MetadataResult(has_exif=False, fields={})

    fields: dict[str, str] = {}
    for tag_id, value in exif_data.items():
        tag_name = TAGS.get(tag_id, str(tag_id))
        # Convert non-string values to strings, skip binary blobs
        if isinstance(value, bytes):
            fields[tag_name] = f"<binary {len(value)} bytes>"
        else:
            fields[tag_name] = str(value)

    return MetadataResult(has_exif=True, fields=fields)
