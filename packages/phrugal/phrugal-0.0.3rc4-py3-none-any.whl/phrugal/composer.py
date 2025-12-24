import logging
from enum import StrEnum, unique, auto
from fractions import Fraction
from pathlib import Path
from typing import List, Tuple

import PIL.Image

from phrugal.composition import ImageComposition
from phrugal.decoration_config import DecorationConfig
from phrugal.image import PhrugalImage, PhrugalPlaceholder

logger = logging.getLogger(__name__)


@unique
class PaddingStrategy(StrEnum):
    PLACEHOLDER = auto()
    DUPLICATE = auto()
    UPSCALE = auto()


class PhrugalComposer:
    DEFAULT_ASPECT_RATIO = Fraction(4, 3)

    def __init__(
        self,
        decoration_config: DecorationConfig,
        input_files=None,
        target_aspect_ratio: Fraction | float = DEFAULT_ASPECT_RATIO,
    ):
        self.decoration_config = decoration_config
        self.input_files = input_files
        self._img_instances: List[PhrugalImage] = []
        self.target_aspect_ratio = Fraction(target_aspect_ratio)
        self._image_groups: List[Tuple[PhrugalImage, ...]] | None = None
        self._padding_strat: PaddingStrategy | None = None

    def create_compositions(
        self,
        output_path: Path | str,
        padding_strategy: PaddingStrategy = PaddingStrategy.UPSCALE,
    ):
        self._padding_strat = padding_strategy
        for in_file in self.input_files:
            img = PhrugalImage(in_file)
            self._img_instances.append(img)

        self._img_instances = sorted(
            self._img_instances, key=lambda x: x.aspect_ratio_normalized, reverse=False
        )
        logger.debug("generate image groups...")
        self._generate_img_groups(
            self._img_instances, self.decoration_config.get_image_count()
        )
        self._process_all_img_groups(output_path)

    def _process_all_img_groups(self, output_path):
        for idx, group in enumerate(self._image_groups):
            logger.info(f"process group {idx + 1}/{len(self._image_groups)}")
            composition_filename = output_path / self._get_filename(group, idx)
            composition = ImageComposition(
                group, target_aspect_ratio=self.target_aspect_ratio
            )
            composition.write_composition(
                filename=composition_filename, decoration_config=self.decoration_config
            )

    def _get_filename(self, group, idx):
        fn = Path(f"img-{idx}")
        return fn.with_suffix(".jpg")

    def discover_images(self, path):
        self.input_files = [p for p in Path(path).glob("**/*.jpg")]
        logger.info(f"discovered {len(self.input_files)} images in {path}")

    def _generate_img_groups(
        self, input_objects: List[PhrugalImage], group_len: int
    ) -> None:
        """Split a list into tuples of size n (last remainder tuple can be smaller)."""
        img_grps = list(zip(*[input_objects[i:] for i in range(group_len)]))
        remainder = input_objects[len(img_grps) * group_len :]

        padding_images_count = group_len - len(remainder)

        if self._padding_strat == PaddingStrategy.UPSCALE:
            pass  # do nothing, upscaling happens automatically
        elif self._padding_strat == PaddingStrategy.PLACEHOLDER:
            ph_image_dims = (int(1000 * self.target_aspect_ratio), 1000)
            # fixme: read padding image color from border config
            ph_image = PIL.Image.new("RGB", ph_image_dims, color="white")
            logger.debug(f"adding {padding_images_count} place holders for padding")
            for placeholder_nr in range(padding_images_count):
                remainder.append(PhrugalPlaceholder(ph_image))
        elif self._padding_strat == PaddingStrategy.DUPLICATE:
            logger.debug(f"adding {padding_images_count} duplicates for padding")
            for duplicate_nr in range(padding_images_count):
                # if more padding images are needed than we have in input, wrap around
                idx_to_duplicate = duplicate_nr % len(input_objects)
                remainder.append(input_objects[idx_to_duplicate])
        else:
            raise RuntimeError("unknown strategy!")

        if remainder:
            img_grps.append(tuple(remainder))
        logger.info(f"generated {len(img_grps)} image groups")

        self._image_groups = img_grps
