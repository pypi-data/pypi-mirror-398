import argparse
import logging
import os
import sys
from pathlib import Path

import phrugal
from phrugal import DecorationConfig
from phrugal.composer import PhrugalComposer

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="phrugal")
    parser.add_argument("-c", "--config", help="Path to custom JSON config")
    parser.add_argument(
        "-i",
        "--input-dir",
        help="Path where the tool will recursively look for images to process.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Path to folder where to locate the output. If omitted, will default to current dir. "
        "The tool will attempt to create a directory if its not yet existing.",
    )
    parser.add_argument(
        "--create-default-config",
        help="If given, create default configuration at given path (or in current directory if omitted) and exit.",
        nargs="?",
        const="",  # the value of no path is given
        default=None,
    )
    parser.add_argument(
        "--version", action="version", version=f"{parser.prog} {phrugal.__version__}"
    )
    return parser


def _phrugal_main(args: argparse.Namespace):
    if args.create_default_config is not None:
        _create_default_config(args.create_default_config)
    elif args.input_dir is None:
        raise RuntimeError(
            "parameter input_dir is needed, refer to --help for help!",
        )
    else:
        input_dir = Path(args.input_dir)
        output_dir = Path(args.output_dir) if args.output_dir else Path(os.getcwd())

        if not output_dir.exists():
            os.makedirs(output_dir, exist_ok=True)

        config = DecorationConfig()
        if args.config:
            config.load_from_file(Path(args.config))
        else:
            config.load_default_config()

        composer = PhrugalComposer(decoration_config=config)
        composer.discover_images(input_dir)
        composer.create_compositions(output_path=output_dir)


def _create_default_config(provided_path: str):
    if provided_path == "":
        current_dir = os.getcwd()
        target_file = Path(current_dir) / "phrugal-default.json"
    else:
        target_file = Path(provided_path)
    pc = phrugal.DecorationConfig()
    pc.write_default_config(target_file)


def run_cli():
    parser = _get_parser()
    parsed_args = parser.parse_args()

    _phrugal_main(parsed_args)


if __name__ == "__main__":
    run_cli()
