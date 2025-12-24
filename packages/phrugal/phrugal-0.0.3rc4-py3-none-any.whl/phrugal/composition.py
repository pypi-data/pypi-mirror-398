import random
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, List

import PIL.Image as pill_image
from PIL.Image import Image, Resampling
from PIL.ImageDraw import Draw

from phrugal.decorated_image import DecoratedPhrugalImage
from phrugal.decoration_config import DecorationConfig
from phrugal.image import PhrugalImage
from phrugal.types import Coordinates

import logging

logger = logging.getLogger(__name__)


def get_contrasting_color():
    colors = ["black", "blue", "green", "red"]
    return random.choice(colors)


@dataclass
class ImageMerge:
    image: Image
    count: int

    @property
    def x(self):
        return self.image.size[0]

    @property
    def y(self):
        return self.image.size[1]

    @property
    def aspect_ratio(self):
        x, y = self.image.size
        return float(x) / float(y)

    def ensure_landscape_orientation(self, rotate_ccw=True):
        is_landscape_orientation = self.aspect_ratio >= 1
        if not is_landscape_orientation:
            self.image = self.image.rotate(90 if rotate_ccw else -90, expand=True)

    def scale_to_dimensions(
        self,
        x_target: int | None = None,
        y_target: int | None = None,
        resample_method: Resampling = Resampling.LANCZOS,
    ) -> None:
        if x_target is None and y_target is None:
            raise RuntimeError("need either x or y dim")
        elif x_target is not None and y_target is not None:
            raise RuntimeError("most not give x and y dim")

        x_prev, y_prev = self.image.size
        if x_target:
            factor = float(x_target) / float(x_prev)
            y_target = y_prev * factor
        else:
            factor = float(y_target) / float(y_prev)
            x_target = x_prev * factor
        already_correct_size = abs(factor - 1) < 1e-5
        if not already_correct_size:
            self.image = self.image.resize(
                (int(x_target), int(y_target)),
                resample=resample_method,
                reducing_gap=4.0,
            )


class ImageComposition:
    def __init__(
        self, images: Iterable[PhrugalImage], target_aspect_ratio: Fraction | float
    ):
        self.images = images
        self.target_aspect_ratio = target_aspect_ratio

    def write_composition(self, filename: Path, decoration_config: DecorationConfig):
        decorated_images = self._get_decorated_images(decoration_config)
        composition = self.get_composition(decorated_images)
        composition.save(filename)

    def get_composition(
        self, decorated_images: Iterable[Image], draw_separator: bool = True
    ) -> Image:
        img_list_to_compose = [ImageMerge(image=im, count=1) for im in decorated_images]
        logger.info("merge decorated images in group...")
        composition = self._merge_image_list(img_list_to_compose, draw_separator)
        return composition.image

    @staticmethod
    def _merge_image_list(
        image_data: List[ImageMerge], draw_separator: bool
    ) -> ImageMerge | None:
        """Recursively merge a list of images until only 1 survives"""
        if not image_data:
            return None
        if len(image_data) == 1:
            logger.debug("done merging images!")
            return image_data[0]
        logger.debug(f"remaining images for merge: {len(image_data)}")
        image_data.sort(key=lambda i: i.count)
        new_merged = ImageComposition._merge_two_images(
            image_data.pop(0), image_data.pop(0)
        )
        image_data.append(new_merged)
        return ImageComposition._merge_image_list(image_data, draw_separator)

    @staticmethod
    def _merge_two_images(
        img_a: ImageMerge, img_b: ImageMerge, draw_separator=True, draw_debug_box=False
    ) -> ImageMerge:
        img_a.ensure_landscape_orientation()
        img_b.ensure_landscape_orientation()

        bigger_x_dim = int(max(img_a.image.size[0], img_b.image.size[0]))
        img_a.scale_to_dimensions(x_target=bigger_x_dim)
        img_b.scale_to_dimensions(x_target=bigger_x_dim)

        new_img = pill_image.new(
            "RGB", (bigger_x_dim, img_a.y + img_b.y), color="white"
        )
        new_img.paste(img_a.image, (int((bigger_x_dim - img_a.x) / 2), 0))
        new_img.paste(img_b.image, (int((bigger_x_dim - img_b.x) / 2), img_a.y))
        if draw_separator:
            ImageComposition._draw_line(new_img, (0, img_a.y), (bigger_x_dim, img_a.y))
        if draw_debug_box:
            ImageComposition._draw_box(
                new_img, (0, 0), new_img.size, color=get_contrasting_color()
            )

        new_count = img_a.count + img_b.count
        merge_returned = ImageMerge(image=new_img, count=new_count)
        merge_returned.ensure_landscape_orientation(
            rotate_ccw=(new_count / 2) % 2 == 0  # rotate cw and ccw every 2 merges
        )
        return merge_returned

    @staticmethod
    def _draw_box(
        img: Image,
        corner_a: Coordinates,
        corner_b: Coordinates,
        color: str = "red",
        width: int = 3,
    ):
        draw = Draw(img)
        a_x, a_y = corner_a
        b_x, b_y = corner_b
        # a_x += 1
        # b_x -= 1
        # a_y += 1
        # b_y -= 1
        coords = [corner_a, (b_x, a_y), corner_b, (a_x, b_y), corner_a]
        draw.line(
            coords,
            fill=color,
            width=width,
        )

    @staticmethod
    def _draw_line(img, start: Coordinates, end: Coordinates):
        draw = Draw(img)
        draw.line([start, end], fill="black", width=1)

    def _get_decorated_images(self, config: DecorationConfig) -> Iterable[Image]:
        decorated_images = []
        for image in self.images:
            logger.info(f"decorating image {image}")
            img_decorated = DecoratedPhrugalImage(
                image, target_aspect_ratio=self.target_aspect_ratio
            )
            img_decorated.config = config
            decorated_images.append(img_decorated.get_decorated_image())
        return decorated_images

    def close_images(self):
        for image in self.images:
            image.close_image()
