import datetime
import time
import unittest

from geopy import Point

import phrugal.geocode


class TestGeocode(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.geocoder = phrugal.geocode.Geocoder()

    def setUp(self):
        self.geocoder._CALLS_MADE = 0  # reset count

    def tearDown(self):
        time.sleep(self.geocoder.MIN_DELAY_SECONDS)  # wait for rate limit expire

    def test_get_location_name_cached(self):
        __ = self.geocoder.get_location_name(49.96233, 9.15892, zoom=18)

        start = datetime.datetime.now()
        for __ in range(1000):
            value = self.geocoder.get_location_name(
                49.96233, 9.15892, zoom=18
            )  # @UnusedVariable
        duration_cached_function_call = datetime.datetime.now() - start

        self.assertLess(
            duration_cached_function_call,
            datetime.timedelta(milliseconds=3),
        )

    def test_get_location_name(self):
        start = datetime.datetime.now()

        result = self.geocoder.get_location_name(45.798333, 24.1512)
        self.assertEqual("Sibiu, Sibiu, România", result)

        result = self.geocoder.get_location_name(45.798333, 24.1512, zoom=14)
        self.assertEqual(
            "Sibiu, Sibiu, România",
            result,
        )

        result = self.geocoder.get_location_name(45.798333, 24.1512, zoom=16)
        self.assertEqual(
            "Piața Mică, Sibiu, Sibiu, România",
            result,
        )

        result = self.geocoder.get_location_name(45.798333, 24.1512, zoom=18)
        self.assertEqual(
            "Piața Mică, Sibiu, Sibiu, România",
            result,
        )

        result = self.geocoder.get_location_name(45.65156, 23.92831, zoom=14)
        self.assertEqual("Sibiu, Sibiu, România", result)

        result = self.geocoder.get_location_name(45.65156, 23.92831, zoom=16)
        self.assertEqual("Transcindrel, Sibiu, Sibiu, România", result)

        result = self.geocoder.get_location_name(45.65156, 23.92831, zoom=18)
        self.assertEqual("Transcindrel, Sibiu, Sibiu, România", result)

        result = self.geocoder.get_location_name(49.80264, 9.95056, zoom=16)
        self.assertEqual("Robert-Koch-Straße, Würzburg, Bayern, Deutschland", result)

        duration = datetime.datetime.now() - start
        self.assertGreater(  # we want to have at least
            duration,
            datetime.timedelta(
                seconds=self.geocoder.MIN_DELAY_SECONDS
                * (self.geocoder._CALLS_MADE - 1)
            ),
        )

    def test_get_location_name_by_point(self):
        variations = [
            "-34.83289, 19.99994",
            "34° 49' 58.4\" S, 19° 59' 59.8\" E",
        ]

        for coordinate_format in variations:
            with self.subTest(f"input: {coordinate_format}"):
                p = Point(coordinate_format)  # type: ignore
                result = self.geocoder.get_location_name_from_point(p, zoom=12)
                self.assertEqual(
                    "Cape Agulhas Local Municipality, Overberg District Municipality, Western Cape, South Africa",
                    result,
                )
