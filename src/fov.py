"""Field-of-view (FOV) masking for fundus photographs.

A fundus photo is a bright circular retina on a black background. Statistics taken over the whole
frame (mean brightness, corner-vs-center contrast, overall color) are dominated by that black border,
so every check that measures image content works on the FOV only.
"""

import cv2
import numpy as np

MIN_FOV_FRACTION = 0.05  # below this the image has no clear retina disc; fall back to the whole frame


def fov_mask(rgb: np.ndarray) -> np.ndarray:
    """Boolean mask of pixels inside the retina disc, eroded a little to skip the blurry rim."""
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    mask = (gray > 20).astype(np.uint8)
    k = max(3, (min(gray.shape) // 100) | 1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((k, k), np.uint8))
    mask = cv2.erode(mask, np.ones((k * 2 + 1, k * 2 + 1), np.uint8))
    if mask.mean() < MIN_FOV_FRACTION:
        return np.ones(gray.shape, dtype=bool)
    return mask.astype(bool)
