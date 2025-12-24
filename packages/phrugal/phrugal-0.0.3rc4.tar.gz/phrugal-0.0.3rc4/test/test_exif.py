import unittest
from datetime import datetime
from pathlib import Path

import phrugal.exif
import phrugal.image


class TestPhrugal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_image_source = Path("./img/exif-data-testdata").glob("**/*.jpg")
        cls.test_instances = [
            phrugal.exif.PhrugalExifData(x) for x in cls.test_image_source
        ]

    def _get_specific_img_instance(self, file_substring):
        return next(
            (x for x in self.test_instances if file_substring in x.image_path.name)
        )

    def test_get_focal_len(self):
        input_and_expected = [
            ("0027", "24mm"),
            ("0095", "0mm"),
        ]
        for img, expected in input_and_expected:
            with self.subTest(f"image: {img}"):
                instance = self._get_specific_img_instance(img)
                actual = instance.get_focal_length()
                self.assertEqual(expected, actual)

    def test_get_aperture(self):
        input_and_expected = [
            ("0027", "f/4.0"),
            ("0095", "inf"),
        ]
        for img, expected in input_and_expected:
            with self.subTest(f"image: {img}"):
                instance = self._get_specific_img_instance(img)
                actual = instance.get_aperture()
                self.assertEqual(expected, actual)

    def test_get_iso(self):
        input_and_expected = [
            ("0027", "ISO 400"),
            ("0028", "ISO 320"),
            ("0040", "ISO 100"),
            ("0047", "ISO 100"),
            ("0095", "ISO 4000"),
        ]
        for img, expected in input_and_expected:
            with self.subTest(f"image: {img}"):
                instance = self._get_specific_img_instance(img)
                actual = instance.get_iso()
                self.assertEqual(expected, actual)

    def test_get_title(self):
        instance = self._get_specific_img_instance("0027")
        with self.assertRaises(NotImplementedError):
            actual = instance.get_title()

    def test_get_description(self):
        instance = self._get_specific_img_instance("0027")
        actual = instance.get_description()
        self.assertEqual(
            'Image of "Casa Luxemburg", taken as test data for a photography helper.',
            actual,
        )

    def test_get_timestamp(self):
        instance = self._get_specific_img_instance("0027")
        actual = instance._get_timestamp_raw()
        expected = datetime(2024, 7, 29, 18, 36, 10)
        self.assertEqual(expected, actual)

    def test_get_gps(self):
        # fmt: off
        input_usedms_includealtitude_expected = [
            ("0027", True, True, "45°47'54.0\"N, 24°9'4.3\"E, 424m"),
            ("0027", False, False, "45°47.900'N, 24°9.072'E"),
            ("0095", True, True, None),
            # does not have altitude info:
            ("37.27", True, True, "45°47'59.4\"N, 24°9'43.6\"E"),
        ]
        # fmt: on
        for (
            img,
            use_dms,
            include_altitude,
            expected,
        ) in input_usedms_includealtitude_expected:
            with self.subTest(f"image: {img}"):
                instance = self._get_specific_img_instance(img)
                actual = instance.get_gps_coordinates(
                    include_altitude=include_altitude, use_dms=use_dms
                )
                self.assertEqual(expected, actual)

    def test_get_geocode(self):
        instance = self._get_specific_img_instance("21.37.27")

        zoom_expected = [
            (8, "Sibiu, România"),
            (12, "Sibiu, Sibiu, România"),
            (14, "Sibiu, Sibiu, România"),
            (16, "Piața 1 Decembrie 1918, Sibiu, Sibiu, România"),
            (20, "Piața 1 Decembrie 1918, Sibiu, Sibiu, România"),
        ]
        for zoom, expected in zoom_expected:
            with self.subTest(f"zoom {zoom}"):
                actual = instance.get_geocode(zoom=zoom)
                expected = expected
                self.assertEqual(expected, actual)

    def test_get_shutter_speed(self):
        # fmt: off
        expected_results = {'1.3s', '1/60s', '1/40s', '1/800s', '1/30s', '1/1250s', '1/500s', '1/25s',
                            '1/640s', '1/80s', '1/125s', '1/50s', '1/8s', '0.6s', '0.8s', '1/2000s',
                            '2.0s', '1/3s', '1/1600s', '1/100s', '1/160s', '1/400s', '1/6s', '1/15s',
                            '1/13s', '1/10s', '1/320s', '1.0s', '1.6s', '1/250s', '1/20s', '1/200s',
                            '1/5s', '1/1000s', '3.2s', '1/2500s', '1/2s', '1/4s'}
        images_without_shutterspeed = [
            "21.37.27"
        ]
        # fmt: on

        for ped in self.test_instances:
            with self.subTest(f"image: {ped.image_path}"):
                ped = phrugal.exif.PhrugalExifData(ped.image_path)
                actual = ped.get_shutter_speed()

                if any(x in ped.image_path.name for x in images_without_shutterspeed):
                    self.assertIsNone(actual)
                else:
                    self.assertIn(actual, expected_results)

    def test_get_image_xp_title(self):
        instance = self._get_specific_img_instance("21.37.27")
        actual = instance.get_image_xp_title()
        expected = "train station"
        self.assertEqual(expected, actual)

    def test_get_image_xp_description(self):
        instance = self._get_specific_img_instance("21.37.27")
        actual = instance.get_image_xp_description()
        expected = "Sibiu train station"
        self.assertEqual(expected, actual)
