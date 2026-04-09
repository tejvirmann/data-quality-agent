"""EyeQ/MCF-Net fundus image quality assessment.

Ported from https://github.com/HzFu/EyeQ
Uses DenseNet121 with multi-color-space fusion (RGB, HSV, LAB).
Outputs: Good / Usable / Reject with confidence scores.
"""

import logging
import os
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
from PIL import Image

from src.config import config
from src.models import FundusAssessment, FundusGrade

logger = logging.getLogger(__name__)

WEIGHTS_DIR = Path("src/ml/weights")
WEIGHTS_FILE = "DenseNet121_v3_v1.tar"
EYEQ_CLASSES = ["good", "usable", "reject"]

# ImageNet normalization (same as EyeQ training)
TRANSFORM = transforms.Compose([
    transforms.Resize(224),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


# --- Model Architecture (from EyeQ repo) ---


class _DenseNet121Base(nn.Module):
    """Single-stream DenseNet121 with sigmoid classifier."""

    def __init__(self, n_class: int):
        super().__init__()
        self.densenet121 = torchvision.models.densenet121(weights=None)
        num_ftrs = self.densenet121.classifier.in_features
        self.densenet121.classifier = nn.Sequential(
            nn.Linear(num_ftrs, n_class),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.densenet121(x)


class MCFNet(nn.Module):
    """Multi-Color-space Fusion Network.

    Three parallel DenseNet121 branches process the image in different
    color spaces (RGB, HSV, LAB), then fuse predictions.
    """

    def __init__(self, n_class: int = 3):
        super().__init__()

        densenet = torchvision.models.densenet121(weights=None)
        num_ftrs = densenet.classifier.in_features

        a_model = _DenseNet121Base(n_class=n_class)
        self.feature_a = a_model
        self.class_a = a_model.densenet121.features

        b_model = _DenseNet121Base(n_class=n_class)
        self.feature_b = b_model
        self.class_b = b_model.densenet121.features

        c_model = _DenseNet121Base(n_class=n_class)
        self.feature_c = c_model
        self.class_c = c_model.densenet121.features

        self.combine1 = nn.Sequential(
            nn.Linear(n_class * 4, n_class),
            nn.Sigmoid(),
        )

        self.combine2 = nn.Sequential(
            nn.Linear(num_ftrs * 3, n_class),
            nn.Sigmoid(),
        )

    def forward(
        self, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor
    ) -> tuple[torch.Tensor, ...]:
        x1 = self.feature_a(x)
        y1 = self.feature_b(y)
        z1 = self.feature_c(z)

        x2 = F.relu(self.class_a(x), inplace=True)
        x2 = F.adaptive_avg_pool2d(x2, (1, 1)).view(x2.size(0), -1)

        y2 = F.relu(self.class_b(y), inplace=True)
        y2 = F.adaptive_avg_pool2d(y2, (1, 1)).view(y2.size(0), -1)

        z2 = F.relu(self.class_c(z), inplace=True)
        z2 = F.adaptive_avg_pool2d(z2, (1, 1)).view(z2.size(0), -1)

        combine = torch.cat(
            (x2.view(x2.size(0), -1), y2.view(y2.size(0), -1), z2.view(z2.size(0), -1)), 1
        )
        combine = self.combine2(combine)

        combine3 = torch.cat(
            (
                x1.view(x1.size(0), -1),
                y1.view(y1.size(0), -1),
                z1.view(z1.size(0), -1),
                combine.view(combine.size(0), -1),
            ),
            1,
        )
        combine3 = self.combine1(combine3)

        return x1, y1, z1, combine, combine3


# --- Inference ---


_model: MCFNet | None = None


def _get_model() -> MCFNet:
    """Load model lazily on first call."""
    global _model
    if _model is not None:
        return _model

    weights_path = Path(config.eyeq_weights_path)
    if not weights_path.exists():
        raise FileNotFoundError(
            f"EyeQ weights not found at {weights_path}. "
            f"Run 'make fetch-model' to download them."
        )

    model = MCFNet(n_class=3)
    checkpoint = torch.load(str(weights_path), map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    _model = model
    logger.info("EyeQ model loaded from %s", weights_path)
    return _model


def _to_color_spaces(image: Image.Image) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Convert PIL image to 3 color-space tensors (RGB, HSV, LAB)."""
    rgb = image.convert("RGB")

    # HSV conversion
    rgb_array = np.array(rgb)
    hsv_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2HSV)
    hsv = Image.fromarray(hsv_array)

    # LAB conversion
    lab_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2LAB)
    lab = Image.fromarray(lab_array)

    rgb_tensor = TRANSFORM(rgb).unsqueeze(0)
    hsv_tensor = TRANSFORM(hsv).unsqueeze(0)
    lab_tensor = TRANSFORM(lab).unsqueeze(0)

    return rgb_tensor, hsv_tensor, lab_tensor


def assess_fundus_quality(image: Image.Image) -> FundusAssessment:
    """Run EyeQ/MCF-Net inference on a fundus image.

    Returns grade (Good/Usable/Reject) with confidence and per-class probabilities.
    """
    model = _get_model()

    rgb_tensor, hsv_tensor, lab_tensor = _to_color_spaces(image)

    with torch.no_grad():
        _, _, _, _, predictions = model(rgb_tensor, hsv_tensor, lab_tensor)

    probs = predictions.squeeze(0).tolist()
    prob_dict = {cls: round(p, 4) for cls, p in zip(EYEQ_CLASSES, probs)}

    best_idx = int(predictions.argmax(dim=1).item())
    grade = FundusGrade(EYEQ_CLASSES[best_idx])
    confidence = round(probs[best_idx], 4)

    return FundusAssessment(
        grade=grade,
        confidence=confidence,
        probabilities=prob_dict,
    )


def download_weights() -> None:
    """Download EyeQ model weights. Called by 'make fetch-model'."""
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = WEIGHTS_DIR / WEIGHTS_FILE

    if dest.exists():
        print(f"Weights already exist at {dest}")
        return

    print(
        f"Download the EyeQ weights manually from the OneDrive link in\n"
        f"https://github.com/HzFu/EyeQ and place them at:\n"
        f"  {dest.resolve()}\n\n"
        f"The file should be named '{WEIGHTS_FILE}' (~112MB)."
    )


if __name__ == "__main__":
    download_weights()
