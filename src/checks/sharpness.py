"""Blur/sharpness detection using Laplacian variance."""

import cv2
import numpy as np
from PIL import Image

from src.config import config
from src.models import SharpnessResult


def check_sharpness(image: Image.Image) -> SharpnessResult:
    """Check image sharpness using Laplacian variance.

    Higher score = sharper image. Typical thresholds:
    - > 150: sharp (good focus)
    - 80-150: borderline (may need review)
    - < 80: blurry (reject)
    """
    gray = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2GRAY)
    score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    if score >= config.sharpness_pass:
        is_sharp = True
        detail = f"Sharp (score: {score:.1f}, threshold: {config.sharpness_pass})"
    elif score >= config.sharpness_review:
        is_sharp = False
        detail = f"Borderline sharpness (score: {score:.1f}, may need review)"
    else:
        is_sharp = False
        detail = f"Blurry (score: {score:.1f}, below minimum {config.sharpness_review})"

    return SharpnessResult(score=score, is_sharp=is_sharp, detail=detail)
