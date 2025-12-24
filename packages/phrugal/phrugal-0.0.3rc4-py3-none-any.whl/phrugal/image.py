import logging
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .types import Dimensions

logger = logging.getLogger(__name__)

MM_PER_INCH = 25.4


@dataclass
class PhrugalImage:
    def __init__(self, file_name: Path | str) -> None:
        self.file_name = Path(file_name)
        self.pillow_image = Image.open(self.file_name, mode="r")
        self.rotation_degrees = 0

    @property
    def image_dims(self) -> Dimensions:
        return self.pillow_image.size

    @property
    def aspect_ratio(self) -> float:
        """y_dim / x_dim"""
        x_dim, y_dim = self.image_dims
        return float(x_dim) / float(y_dim)

    @property
    def aspect_ratio_normalized(self) -> float:
        """Same as aspect ratio, but assume that we rotate portrait orientation to landscape always"""
        return self.aspect_ratio if self.aspect_ratio > 1 else 1 / self.aspect_ratio

    def rotate_90_deg_ccw(self):
        rotated_img = self.pillow_image.rotate(90, expand=True)
        self.rotation_degrees += 90
        self.pillow_image = rotated_img

    def close_image(self):
        self.pillow_image.close()

    def __repr__(self):
        return f"{self.file_name.name}"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pillow_image.close()
        return False

    def __del__(self):
        try:
            self.pillow_image.close()
        except AttributeError:  # if open fails, we will not have self.image, ignore it
            pass


class PhrugalPlaceholder(PhrugalImage):
    def __init__(self, img: Image) -> None:
        self.file_name = None
        self.pillow_image = img
        self.rotation_degrees = 0
