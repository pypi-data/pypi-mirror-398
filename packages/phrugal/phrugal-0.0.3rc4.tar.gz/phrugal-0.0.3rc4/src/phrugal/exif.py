import datetime
import logging
from collections import namedtuple
from pathlib import Path
from typing import Optional, Tuple, Iterable

import exifread
from exifread.classes import IfdTag
from exifread.utils import Ratio
from geopy import Point

from .geocode import Geocoder

logger = logging.getLogger(__name__)

GpsData = namedtuple("GpsData", ["lat", "lat_ref", "lon", "lon_ref", "altitude"])


def get_common_values() -> list[float]:
    """Provide a sequence of commonly used values.

    Since there is no easy rule for these values, they are hard coded.
    """
    # fmt: off
    base_values = {
        2500, 2000, 1600, 1250, 1000,
        800, 640, 500, 400, 320, 250, 200, 160, 125, 100,
        80, 60, 50, 40, 30, 25, 20, 15, 13, 10,
        8, 6, 5, 4, 2,
    }
    # fmt: on
    retval = sorted([float(x) for x in base_values])
    return retval


class PhrugalExifData:
    COMMON_DIVIDEND_VALUES = get_common_values()
    THRESHOLD_COMMON_DISPLAY = (
        0.08  # how many deviation is allowed before "snapping" onto common value
    )
    THRESHOLD_FRACTION_DISPLAY = (
        0.55  # smaller values are displayed as fractions of seconds
    )
    THRESHOLD_APERTURE_INF = 1e8  # bigger values are considered infinite/tiny
    INF_APERTURE_REPRESENTATION = "inf"  # represent tiny apertures like this
    EXTRACT_APPLICATION_NOTES = False  # needed, once we implement get_title()

    def __init__(self, image_path: Path | str) -> None:
        self.image_path = image_path
        self.geocoder = Geocoder()
        self._parse_exif()

    def _parse_exif(self):
        if self.image_path:
            with open(self.image_path, "rb") as fp:
                self.exif_data = exifread.process_file(
                    fp, debug=self.EXTRACT_APPLICATION_NOTES  # type: ignore
                )
        else:
            self.exif_data = dict()

    def __repr__(self):
        return f"exif: {Path(self.image_path).name}"

    def get_focal_length(self) -> str | None:
        raw = self.exif_data.get("EXIF FocalLength", None)  # type: Optional[IfdTag]
        if raw is None:
            return None
        else:
            value = float(raw.values[0])
            return f"{value:1.0f}mm"

    def get_aperture(self) -> str | None:
        raw = self.exif_data.get("EXIF ApertureValue", None)  # type: Optional[IfdTag]
        if raw is None:
            return None
        else:
            value = float(raw.values[0])
            if value > self.THRESHOLD_APERTURE_INF:
                return str(self.INF_APERTURE_REPRESENTATION)
            return f"f/{value:.1f}"

    def get_shutter_speed(self, use_nominal_value: bool = True) -> str | None:
        """Return the shutter speed/

        :param use_nominal_value: if set, round the values to nominal values (instead of the more
                                  precise, recorded values. See also
                                  https://www.scantips.com/lights/fstop2.html.
        :return: formatted string
        """
        raw = self.exif_data.get(
            "EXIF ShutterSpeedValue", None
        )  # type: Optional[IfdTag]
        if raw is None:
            return None
        else:
            apex = raw.values[0]
            exposure_time = 2 ** (-apex)
            exposure_dividend = 2**apex
            if exposure_time < self.THRESHOLD_FRACTION_DISPLAY:
                if use_nominal_value:
                    exposure_dividend = self._round_shutter_to_common_value(
                        float(exposure_dividend)
                    )
                div_rounded = int(exposure_dividend)
                return f"1/{div_rounded}s"
            else:
                return f"{exposure_time:.1f}s"

    def get_iso(self) -> str | None:
        raw = self.exif_data.get("EXIF ISOSpeedRatings", None)  # type: Optional[IfdTag]
        if raw is None:
            return None
        else:
            return f"ISO {raw}"

    def get_title(self) -> str | None:
        """Return the title.

        This is not yet implemented. In order to get the title, we need to tell exifread
        to use the debug mode, this also gives us the "Image ApplicationNotes" tag.

        The application notes are XML formatted, and also include the title.

        app_notes_xml = self.exif_data.get("Image ApplicationNotes", None)

        The current implementation skips title, since it slows down exif read and other features
        are more important.
        """
        raise NotImplementedError("get_title not yet implemented")

    def get_description(self) -> str | None:
        raw = self.exif_data.get("Image ImageDescription", None)
        if raw is None:
            return None
        else:
            return str(raw)

    def get_image_xp_title(self) -> str:
        raw = self.exif_data.get("Image XPTitle", None)  # type: Optional[IfdTag]
        return self._get_str_from_utf16(raw.values) if raw else None

    def get_image_xp_description(self) -> str:
        raw = self.exif_data.get("Image XPSubject", None)  # type: Optional[IfdTag]
        return self._get_str_from_utf16(raw.values) if raw else None

    def get_timestamp(self, format: str = "%Y:%m:%d %H:%M") -> str:
        ts_raw = self._get_timestamp_raw()
        return ts_raw.strftime(format) if ts_raw else None

    def get_gps_coordinates(
        self, include_altitude: bool = True, use_dms: bool = True
    ) -> str | None:
        gps_data = self._get_gps_raw()

        have_gps_fix = all(
            [gps_data.lat, gps_data.lat_ref, gps_data.lon, gps_data.lon_ref]
        )
        have_altitude = gps_data.altitude is not None

        if have_gps_fix:
            gps_formatted = self._format_gps_coordinates(
                gps_data, format="dms" if use_dms else "dds"
            )

            if have_altitude and include_altitude:
                altidue_value = float(gps_data.altitude.values[0])
                gps_formatted += f", {altidue_value:1.0f}m"
        else:
            return None
        return gps_formatted

    def get_geocode(self, zoom=12):
        gps_coordinates_formatted = self.get_gps_coordinates(include_altitude=False)
        if gps_coordinates_formatted:
            location = Point(gps_coordinates_formatted)  # type: ignore
            location_geocoded = self.geocoder.get_location_name_from_point(
                location, zoom=zoom
            )
        else:
            location_geocoded = None
        return location_geocoded

    def get_camera_model(self):
        raw = self.exif_data.get("Image Model", None)  # type: Optional[IfdTag]
        return str(raw.values) if raw else None

    def get_lens_model(self):
        raw = self.exif_data.get("EXIF LensModel", None)  # type: Optional[IfdTag]
        return str(raw.values) if raw else None

    @classmethod
    def _format_gps_coordinates(cls, gps_data: GpsData, format: str = "dms") -> str:
        lat_deg, lat_min, lat_sec = gps_data.lat
        lon_deg, lon_min, lon_sec = gps_data.lon

        # fmt: off
        if format == "dms":  # degree, minute, second
            lat_formatted = f"{lat_deg:1.0f}°{lat_min:1.0f}'{lat_sec:1.1f}\"{str(gps_data.lat_ref)}"
            lon_formatted = f"{lon_deg:1.0f}°{lon_min:1.0f}'{lon_sec:1.1f}\"{str(gps_data.lon_ref)}"
        elif format == "dds":  # degree, decimal minute
            lat_min += lat_sec / 60
            lon_min += lon_sec / 60
            lat_formatted = f"{lat_deg:1.0f}°{lat_min:1.3f}'{str(gps_data.lat_ref)}"
            lon_formatted = f"{lon_deg:1.0f}°{lon_min:1.3f}'{str(gps_data.lon_ref)}"
        else:
            raise ValueError(f"Unsupported format: {format}")
        # fmt: on
        return f"{lat_formatted}, {lon_formatted}"

    @staticmethod
    def _ratios_to_coordinates(data: list[Ratio]) -> Tuple[float, float, float]:
        """Convert exif specific list of ratios into a tuple of degree, arc minute, arc seconds"""
        degree = float(data[0])
        minute = float(data[1])
        second = float(data[2])

        remainder_degree = degree - int(degree)
        degree -= remainder_degree
        minute += remainder_degree * 60

        remainder_minute = minute - int(minute)
        minute -= remainder_minute
        second += remainder_minute * 60

        return degree, minute, second

    def _round_shutter_to_common_value(self, dividend: float) -> float:
        closest_common_value = min(
            self.COMMON_DIVIDEND_VALUES, key=lambda a: abs(a - dividend)
        )
        deviation_from_closest = abs(dividend - closest_common_value) / dividend

        if deviation_from_closest > self.THRESHOLD_COMMON_DISPLAY:
            return dividend
        else:
            return closest_common_value

    @staticmethod
    def _get_str_from_utf16(values: Iterable) -> str:
        decoded = bytes(values).decode("utf-16")
        return decoded.rstrip("\x00")

    def _get_timestamp_raw(self) -> datetime.datetime | None:
        raw = self.exif_data.get("EXIF DateTimeOriginal", None)
        if raw is None:
            return None
        else:
            exif_ts_format = "%Y:%m:%d %H:%M:%S"
            return datetime.datetime.strptime(str(raw), exif_ts_format)

    def _get_gps_raw(self) -> GpsData:
        lat = self.exif_data.get("GPS GPSLatitude", None)  # type: Optional[IfdTag]
        lat_ref = self.exif_data.get("GPS GPSLatitudeRef", None)
        lon = self.exif_data.get("GPS GPSLongitude", None)  # type: Optional[IfdTag]
        lon_ref = self.exif_data.get("GPS GPSLongitudeRef", None)
        alt = self.exif_data.get("GPS GPSAltitude", None)  # type: Optional[IfdTag]
        return GpsData(
            self._ratios_to_coordinates(lat.values) if lat else None,
            lat_ref,
            self._ratios_to_coordinates(lon.values) if lon else None,
            lon_ref,
            alt,
        )
