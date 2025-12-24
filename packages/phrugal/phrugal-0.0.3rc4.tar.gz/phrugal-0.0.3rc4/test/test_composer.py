import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from phrugal.composer import PhrugalComposer
from phrugal.decoration_config import DecorationConfig


class TestPhrugalComposer(unittest.TestCase):
    def setUp(self):
        self.test_data_path = Path("./img/aspect-ratio")
        self._temp_dir = TemporaryDirectory(prefix="phrugal-test")
        self.temp_path = Path(self._temp_dir.name)
        self.deco_config = DecorationConfig()
        self.deco_config.load_default_config()

    def tearDown(self):
        self._temp_dir.cleanup()

    def test_constructor(self):
        composer = PhrugalComposer(decoration_config=self.deco_config)
        self.assertAlmostEqual(4.0 / 3.0, composer.target_aspect_ratio)

        composer = PhrugalComposer(decoration_config=self.deco_config, target_aspect_ratio=0.1)
        self.assertAlmostEqual(0.1, composer.target_aspect_ratio)

    def test_discover_images(self):
        composer = PhrugalComposer(decoration_config=self.deco_config)
        composer.discover_images(self.test_data_path)
        expected = [
            "img\\aspect-ratio\\100x600.jpg",
            "img\\aspect-ratio\\300x450.jpg",
            "img\\aspect-ratio\\360x240.jpg",
            "img\\aspect-ratio\\400x400.jpg",
            "img\\aspect-ratio\\400x600.jpg",
            "img\\aspect-ratio\\600x100.jpg",
            "img\\aspect-ratio\\600x400.jpg",
            "img\\aspect-ratio\\600x500.jpg",
            "img\\aspect-ratio\\600x600.jpg",
        ]
        self.assertListEqual(expected, [str(x) for x in composer.input_files])

    def test_create_composition(self):
        composer = PhrugalComposer(decoration_config=self.deco_config)
        composer.discover_images(self.test_data_path)
        composer.create_compositions(output_path=self.temp_path)
