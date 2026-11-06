"""Color space validation and channel balance checking for fundus images."""

import numpy as np
from PIL import Image

from src.config import config
from src.fov import fov_mask
from src.models import ColorResult


def check_color(image: Image.Image) -> ColorResult:
    """Validate color mode and that the retina has a normal fundus color profile.

    A healthy fundus photo is strongly red-orange: red >> green > blue. Channel *equality* is the
    wrong test (it would fail every real fundus photo). Instead the retina's mean green/red and
    blue/red ratios must fall in a plausible range. A blue cast or a grayscale/washed-out image fails.
    """
    mode = image.mode
    channels = len(image.getbands())

    if mode in ("L", "LA"):
        return ColorResult(
            mode=mode, channels=channels, balanced=False,
            channel_means=[round(float(np.mean(np.array(image.convert("L")))), 2)],
            detail=f"Grayscale image ({mode}); fundus images should be RGB color",
        )

    rgb = np.array(image.convert("RGB"))
    mask = fov_mask(rgb)
    r, g, b = (float(rgb[:, :, i][mask].mean()) for i in range(3))
    channel_means = [round(r, 2), round(g, 2), round(b, 2)]
    gr = g / max(r, 1.0)
    br = b / max(r, 1.0)

    balanced = config.color_gr_min <= gr <= config.color_gr_max and br <= config.color_br_max
    if balanced:
        detail = f"Normal fundus color (G/R {gr:.2f}, B/R {br:.2f})"
    elif br > config.color_br_max or b > r:
        detail = f"Blue/cool color cast (G/R {gr:.2f}, B/R {br:.2f})"
    elif gr > config.color_gr_max:
        detail = f"Washed-out or grayscale-like color (G/R {gr:.2f})"
    else:
        detail = f"Over-saturated red (G/R {gr:.2f})"

    return ColorResult(mode=mode, channels=channels, balanced=balanced, channel_means=channel_means, detail=detail)
