"""Illumination analysis: brightness, uniformity, vignetting, measured inside the retina."""

import cv2
import numpy as np
from PIL import Image

from src.config import config
from src.fov import fov_mask
from src.models import IlluminationResult


def check_illumination(image: Image.Image) -> IlluminationResult:
    """Analyze illumination over the retina disc (the black border of a fundus photo is ignored).

    Checks:
    - Mean brightness (under/overexposure)
    - Brightness standard deviation (uniformity)
    - Vignetting: outer retina much darker than the center
    """
    rgb = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    mask = fov_mask(rgb)
    mean_brightness = float(gray[mask].mean())
    std_brightness = float(gray[mask].std())

    h, w = gray.shape
    yy, xx = np.mgrid[:h, :w]
    radius = np.hypot(yy - h / 2, xx - w / 2) / (min(h, w) / 2)
    center = mask & (radius < 0.4)
    outer = mask & (radius > 0.7)
    center_mean = float(gray[center].mean()) if center.any() else mean_brightness
    outer_mean = float(gray[outer].mean()) if outer.any() else center_mean
    vignetting_detected = center_mean > 0 and (outer_mean / center_mean) < config.vignetting_ratio_min

    uniform = std_brightness < config.brightness_std_pass

    parts = []
    if mean_brightness < config.brightness_min_pass:
        parts.append(f"Underexposed (mean {mean_brightness:.0f})")
    elif mean_brightness > config.brightness_max_pass:
        parts.append(f"Overexposed (mean {mean_brightness:.0f})")
    else:
        parts.append(f"Brightness OK (mean {mean_brightness:.0f})")
    if not uniform:
        parts.append(f"Non-uniform illumination (std {std_brightness:.0f})")
    if vignetting_detected:
        parts.append(f"Vignetting (outer {outer_mean:.0f} vs center {center_mean:.0f})")

    in_range = config.brightness_min_pass <= mean_brightness <= config.brightness_max_pass
    return IlluminationResult(
        mean_brightness=round(mean_brightness, 2),
        std_brightness=round(std_brightness, 2),
        uniform=uniform and in_range and not vignetting_detected,
        vignetting_detected=vignetting_detected,
        detail="; ".join(parts),
    )
