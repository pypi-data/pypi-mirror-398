import argparse
import contextlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest import mock, TestCase

from phrugal.cli import run_cli


@contextlib.contextmanager
def new_cd(x):
    """See https://stackoverflow.com/a/75049063/849959"""
    d = os.getcwd()

    # This could raise an exception, but it's probably
    # best to let it propagate and let the caller
    # deal with it, since they requested x
    os.chdir(x)

    try:
        yield

    finally:
        # This could also raise an exception, but you *really*
        # aren't equipped to figure out what went wrong if the
        # old working directory can't be restored.
        os.chdir(d)


class TestCli(TestCase):
    def setUp(self):
        super().setUp()
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.tempdir)

    @mock.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(create_default_config=""),
    )
    def test_create_default_config_no_location(self, mock_args):
        with new_cd(self.tempdir):
            run_cli()
            expected_file = Path(self.tempdir) / "phrugal-default.json"
            self.assertTrue(expected_file.exists())

    @mock.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(create_default_config="./foo.json"),
    )
    def test_create_default_config(self, mock_args):
        with new_cd(self.tempdir):
            run_cli()
            expected_file = Path(self.tempdir) / "foo.json"
            self.assertTrue(expected_file.exists())
            with open(expected_file) as fp:
                content = json.load(fp)
                expected_subset = {"top_left": {"description": {}}}
                self.assertDictEqual(content, content | expected_subset)
