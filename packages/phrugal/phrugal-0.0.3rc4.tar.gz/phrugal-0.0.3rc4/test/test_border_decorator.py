import itertools
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from phrugal.decorated_image import DecoratedPhrugalImage
from phrugal.image import PhrugalImage


class TestBorderDecorator(TestCase):
    def setUp(self):
        self.test_data_path = Path("./img/aspect-ratio")
        self._temp_dir = TemporaryDirectory(prefix="phrugal-test")
        self.temp_path = Path(self._temp_dir.name)

        self.img_path_landscape_extreme = self.test_data_path / "100x600.jpg"
        self.img_path_portrait_extreme = self.test_data_path / "100x600.jpg"
        self.img_path_square = self.test_data_path / "400x400.jpg"
        self.img_path_landscape_regular = self.test_data_path / "600x400.jpg"
        self.img_path_portrait_regular = self.test_data_path / "400x600.jpg"

    def tearDown(self):
        self._temp_dir.cleanup()

    def test_constructor(self):
        base_img = PhrugalImage(self.img_path_portrait_extreme)
        __ = DecoratedPhrugalImage(base_img)

    def test_get_padded_dimensions(self):
        base_images = [
            self.img_path_square,
            self.img_path_landscape_regular,
            self.img_path_landscape_extreme,
            self.img_path_portrait_regular,
            self.img_path_portrait_extreme,
        ]
        # fmt: off
        target_aspect_ratios = [
            1.0,
            4.0 / 3.0,
            0.5
        ]
        # fmt: on

        for t_ar, bi in itertools.product(target_aspect_ratios, base_images):
            with self.subTest(f" target ratio: {t_ar:1.3f}, img: {bi}"):
                base_img = PhrugalImage(bi)
                decorator = DecoratedPhrugalImage(base_img, target_aspect_ratio=t_ar)
                padded_dimensions = decorator.get_padded_dimensions()
                actual_ratio = padded_dimensions[0] / padded_dimensions[1]
                test_parameters = (
                    f"target ar: {t_ar}, actual ar: {actual_ratio}, image: {bi}"
                )
                """
                note on test tolerance: we end up with whole pixel dimensions, so
                there will always be some inaccuracy.
                a better (more complicated test) would check for a target ratio
                that is as close as possible (i.e. ignore deviations that are within 1 pixel
                at that given image size
                """
                self.assertAlmostEqual(
                    t_ar, actual_ratio, 2, msg=f"fail at {test_parameters}"
                )
