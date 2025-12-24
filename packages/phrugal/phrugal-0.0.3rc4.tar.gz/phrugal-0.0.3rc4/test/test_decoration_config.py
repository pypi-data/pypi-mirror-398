import json
import os
import tempfile
import unittest

from phrugal.decoration_config import DecorationConfig


class TestDecorationConfig(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.tempfiles: list[tempfile.NamedTemporaryFile] = []

    def tearDown(self):
        super().tearDown()
        for tf in self.tempfiles:
            os.unlink(tf.name)

    def test_constructor(self):
        dc = DecorationConfig()
        self.assertDictEqual(dict(), dc._config)

    def test_load_defaults(self):
        dc = DecorationConfig()
        self.assertDictEqual(dict(), dc._config)

        dc.load_default_config()
        # we test only 1 value as a stand in for successful default config load
        expected = {"gps_coordinates": {"use_dms": True}}
        self.assertDictEqual(expected, dc._config.get("bottom_right"))

    def test_load_from_file(self):
        test_config = {"test_key": "test_value"}
        tf = tempfile.NamedTemporaryFile(mode="w+t", delete=False)
        self.tempfiles.append(tf)

        tf.write(json.dumps(test_config, indent=2))
        tf.close()

        dc = DecorationConfig()
        dc.load_from_file(tf.name)
        self.assertDictEqual(test_config, dc._config)


    def test_write_default_config(self):
        tf = tempfile.NamedTemporaryFile(mode="w+t", delete=False)
        self.tempfiles.append(tf)
        dc = DecorationConfig()
        dc.write_default_config(tf.name)
        tf.close()


        with open(tf.name) as def_config_fp:
            actual = json.load(def_config_fp)
            expected_subset = {"top_left": {"description": {}}}
            self.assertDictEqual(actual, actual | expected_subset)



if __name__ == "__main__":
    unittest.main()
