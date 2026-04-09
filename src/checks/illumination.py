"""Illumination analysis: brightness, uniformity, vignetting detection."""

import cv2
import numpy as np
from PIL import Image

from src.config import config
from src.models import IlluminationResult


def check_illumination(image: Image.Image) -> IlluminationResult:
    """Analyze image illumination quality.

    Checks:
    - Mean brightness (over/underexposure)
    - Brightness standard deviation (uniformity)
    - Vignetting (dark corners relative to center)
    """
    gray = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2GRAY)
    mean_brightness = float(np.mean(gray))
    std_brightness = float(np.std(gray))

    # Vignetting detection: compare center vs corners
    h, w = gray.shape
    center_region = gray[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
    corner_tl = gray[: h // 8, : w // 8]
    corner_tr = gray[: h // 8, 7 * w // 8 :]
    corner_bl = gray[7 * h // 8 :, : w // 8]
    corner_br = gray[7 * h // 8 :, 7 * w // 8 :]

    center_mean = float(np.mean(center_region))
    corners_mean = float(
        np.mean(np.concatenate([corner_tl.ravel(), corner_tr.ravel(), corner_bl.ravel(), corner_br.ravel()]))
    )
    # Vignetting if corners are significantly darker than center
    vignetting_detected = (center_mean - corners_mean) > 40

    # Uniformity check
    uniform = std_brightness < config.brightness_std_pass

    # Build detail message
    parts = []
    if mean_brightness < config.brightness_min_pass:
        parts.append(f"Underexposed (mean: {mean_brightness:.1f})")
    elif mean_brightness > config.brightness_max_pass:
        parts.append(f"Overexposed (mean: {mean_brightness:.1f})")
    else:
        parts.append(f"Brightness OK (mean: {mean_brightness:.1f})")

    if not uniform:
        parts.append(f"Non-uniform illumination (std: {std_brightness:.1f})")
    if vignetting_detected:
        parts.append(f"Vignetting detected (center: {center_mean:.0f}, corners: {corners_mean:.0f})")

    return IlluminationResult(
        mean_brightness=round(mean_brightness, 2),
        std_brightness=round(std_brightness, 2),
        uniform=uniform,
        vignetting_detected=vignetting_detected,
        detail="; ".join(parts),
    )
