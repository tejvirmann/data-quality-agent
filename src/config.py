"""Quality threshold configuration. All values are overridable via environment variables."""

from pydantic_settings import BaseSettings


class QualityConfig(BaseSettings):
    """All quality thresholds. Override via env vars prefixed with QUALITY_."""

    model_config = {"env_prefix": "QUALITY_"}

    # Sharpness (Laplacian variance)
    sharpness_pass: float = 150.0
    sharpness_review: float = 80.0

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

    # Color balance (max difference between channel means)
    color_balance_pass: float = 30.0
    color_balance_review: float = 50.0

    # Allowed image formats
    allowed_formats: list[str] = ["JPEG", "PNG", "TIFF", "BMP"]

    # EyeQ model
    eyeq_weights_path: str = "src/ml/weights/DenseNet121_v3_v1.tar"
    eyeq_enabled: bool = True


config = QualityConfig()
