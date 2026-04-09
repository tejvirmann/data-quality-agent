"""Color space validation and channel balance checking."""

import numpy as np
from PIL import Image

from src.config import config
from src.models import ColorResult


def check_color(image: Image.Image) -> ColorResult:
    """Validate color space and check channel balance.

    Fundus images should be RGB with reasonably balanced channels.
    Extreme tint (e.g., all-red) indicates a capture or processing problem.
    """
    mode = image.mode
    channels = len(image.getbands())

    # Convert to RGB for analysis if possible
    if mode in ("L", "LA"):
        balanced = True
        channel_means = [float(np.mean(np.array(image.convert("L"))))]
        detail = f"Grayscale image ({mode}); fundus images should be RGB"
        return ColorResult(
            mode=mode, channels=channels, balanced=balanced,
            channel_means=channel_means, detail=detail,
        )

    rgb = np.array(image.convert("RGB"), dtype=np.float64)
    r_mean = float(np.mean(rgb[:, :, 0]))
    g_mean = float(np.mean(rgb[:, :, 1]))
    b_mean = float(np.mean(rgb[:, :, 2]))
    channel_means = [round(r_mean, 2), round(g_mean, 2), round(b_mean, 2)]

    # Max difference between any two channels
    max_diff = max(abs(r_mean - g_mean), abs(r_mean - b_mean), abs(g_mean - b_mean))
    balanced = max_diff < config.color_balance_pass

    if balanced:
        detail = f"Color balance OK (max channel diff: {max_diff:.1f})"
    elif max_diff < config.color_balance_review:
        detail = f"Slight color imbalance (max diff: {max_diff:.1f}, review recommended)"
    else:
        detail = f"Severe color imbalance (max diff: {max_diff:.1f})"

    return ColorResult(
        mode=mode,
        channels=channels,
        balanced=balanced,
        channel_means=channel_means,
        detail=detail,
    )
