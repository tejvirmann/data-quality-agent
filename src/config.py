"""Quality threshold configuration. All values are overridable via environment variables."""

from pydantic_settings import BaseSettings


class QualityConfig(BaseSettings):
    """All quality thresholds. Override via env vars prefixed with QUALITY_."""

    model_config = {"env_prefix": "QUALITY_"}

    # Sharpness: normalized Laplacian variance inside the retina (see checks/sharpness.py).
    # Calibrated on a small sample set; re-tune on real reading-center images.
    sharpness_pass: float = 3.5
    sharpness_review: float = 1.5

    # Resolution
    min_width: int = 1024
    min_height: int = 1024

    # Illumination
    brightness_min_pass: float = 60.0
    brightness_max_pass: float = 200.0
    brightness_min_review: float = 40.0
    brightness_max_review: float = 230.0
    brightness_std_pass: float = 60.0
    brightness_std_review: float = 80.0

    # Vignetting: outer retina brightness / center brightness below this is flagged
    vignetting_ratio_min: float = 0.6

    # Fundus color profile: retina mean green/red and blue/red ratios (healthy images are red-orange)
    color_gr_min: float = 0.25
    color_gr_max: float = 0.85
    color_br_max: float = 0.7

    # Allowed image formats
    allowed_formats: list[str] = ["JPEG", "PNG", "TIFF", "BMP"]

    # EyeQ model
    eyeq_weights_path: str = "src/ml/weights/DenseNet121_v3_v1.tar"
    eyeq_enabled: bool = True


config = QualityConfig()
