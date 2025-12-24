import logging
from functools import cache

from geopy import Point
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

import phrugal

logger = logging.getLogger(__name__)

USER_AGENT = f"phrugal/{phrugal.__version__} (+https://github.com/0x6d64/phrugal)"


def get_geocoder() -> Nominatim:
    return Nominatim(user_agent=USER_AGENT)


class Geocoder:
    GEOCODER = None
    _CALLS_MADE = 0
    MIN_DELAY_SECONDS = 1.1
    ERROR_WAIT_SECONDS = 7
    MAX_RETRIES = 5
    DEFAULT_ZOOM = 12

    def __init__(self):
        if self.GEOCODER is None:
            self.GEOCODER = get_geocoder()
            self._reverse_rate_limited = RateLimiter(
                self.GEOCODER.reverse,
                min_delay_seconds=self.MIN_DELAY_SECONDS,
                max_retries=self.MAX_RETRIES,
                error_wait_seconds=self.ERROR_WAIT_SECONDS,
            )

    @cache
    def get_location_name(
        self, lat: float, lon: float, zoom: int = DEFAULT_ZOOM
    ) -> str:
        """Returns a name for given coordinates

        Note: The selection of the values that are returned and omitted are highly subjective.
        This is since in e.g. Germany the neighbourhood value does not match the real world name
        that people use for the location.

        :param lat: latitude
        :param lon: longitude
        :param zoom: zoom level, see https://nominatim.org/release-docs/develop/api/Reverse/#result-restriction
        :return: formatted location name
        """
        loc = Point(lat, lon)
        return self.get_location_name_from_point(loc, zoom=zoom)

    def get_location_name_from_point(self, loc: Point, zoom: int = DEFAULT_ZOOM) -> str:
        answer = self._reverse_rate_limited(loc, exactly_one=True, zoom=zoom)
        self._CALLS_MADE += 1
        address_dict = answer.raw["address"]
        name_parts = [
            address_dict.get("road"),
            address_dict.get("city"),
            address_dict.get("county"),
            address_dict.get("state"),
            address_dict.get("country"),
        ]
        name_formatted = ", ".join(x for x in name_parts if x)
        return name_formatted
