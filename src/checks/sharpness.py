"""Blur/sharpness detection using normalized Laplacian variance inside the retina."""

import cv2
import numpy as np
from PIL import Image

from src.config import config
from src.fov import fov_mask
from src.models import SharpnessResult

_WORK_WIDTH = 512  # score at a fixed scale so a 12MP and a 2MP photo of the same focus score alike


def check_sharpness(image: Image.Image) -> SharpnessResult:
    """Measure focus as Laplacian variance of the green channel, inside the retina only.

    The green channel carries the most vessel contrast in fundus images. The variance is divided by
    the squared mean brightness so a dark but well-focused image is not mistaken for a blurry one.
    Higher is sharper.

    The defaults are calibrated on a small set of sample images; tune sharpness_pass and
    sharpness_review (QUALITY_SHARPNESS_*) on real reading-center data before relying on them.
    """
    rgb = np.array(image.convert("RGB"))
    h, w = rgb.shape[:2]
    small = cv2.resize(rgb, (_WORK_WIDTH, max(1, round(h * _WORK_WIDTH / w))), interpolation=cv2.INTER_AREA)
    mask = fov_mask(small)
    green = small[:, :, 1].astype(np.float64)
    mean_g = max(float(green[mask].mean()), 1.0)
    score = float(cv2.Laplacian(green, cv2.CV_64F)[mask].var()) / (mean_g**2) * 1000

    if score >= config.sharpness_pass:
        return SharpnessResult(score=round(score, 2), is_sharp=True,
                               detail=f"Sharp (score {score:.1f}, pass at {config.sharpness_pass})")
    if score >= config.sharpness_review:
        return SharpnessResult(score=round(score, 2), is_sharp=False,
                               detail=(f"Borderline focus (score {score:.1f}, between "
                                       f"{config.sharpness_review} and {config.sharpness_pass}): review"))
    return SharpnessResult(score=round(score, 2), is_sharp=False,
                           detail=f"Blurry (score {score:.1f}, below {config.sharpness_review})")
