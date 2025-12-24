import json
import logging
from pathlib import Path

from .exif import PhrugalExifData

logger = logging.getLogger(__name__)


class DecorationConfig:
    DEFAULT_CONFIG = {
        "image_count": 4,
        "bottom_left": {
            "focal_length": {},
            "aperture": {},
            "shutter_speed": {"use_nominal_value": True},
            "iso": {},
        },
        "bottom_right": {
            "gps_coordinates": {"use_dms": True},
        },
        "top_left": {
            "description": {},
        },
        "top_right": {
            "timestamp": {"format": "%Y-%m-%dT%H:%M"},
            "geocode": {"zoom": 12},
        },
    }

    def __init__(self, item_separator: str = " | "):
        self.item_separator = item_separator
        self._config = dict()

    def load_from_file(self, config_file: Path | str):
        with open(config_file, "r") as cf:
            self._config = json.load(cf)

    def write_default_config(self, config_file: Path | str):
        self._write_config(config_file, self.DEFAULT_CONFIG)

    @staticmethod
    def _write_config(config_file: Path | str, config: dict):
        with open(config_file, "w") as cf:
            json.dump(config, cf, indent=4)

    def load_default_config(self):
        """Some default values, created mostly for debug purposes."""
        self._config = self.DEFAULT_CONFIG

    def get_image_count(self) -> int:
        try:
            ic = int(self._config.get("image_count", None))  # type: ignore
        except TypeError:
            raise RuntimeError("Did not find integer image_count in config.")
        return ic

    def get_string_at_corner(self, exif: PhrugalExifData, corner: str) -> str:
        valid_corners = ["bottom_left", "bottom_right", "top_left", "top_right"]
        assert corner in valid_corners
        result_string = self._build_configured_string(exif, self._config.get(corner))
        return result_string

    def _build_configured_string(
        self, exif: PhrugalExifData, configured_items: dict
    ) -> str:
        result_fragments = []
        for item in configured_items.items():
            item_name, item_config_params = item
            exif_getter_name = f"get_{item_name}"
            if not hasattr(exif, exif_getter_name):
                raise ValueError(f"item {item_name} not implemented")
            getter = getattr(exif, exif_getter_name)
            if item_config_params:
                single_fragment = getter(**item_config_params)
            else:
                single_fragment = getter()
            result_fragments.append(single_fragment)
        return self.item_separator.join((x for x in result_fragments if x))
