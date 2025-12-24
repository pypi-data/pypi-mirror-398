# Copyright (C) 2024,2025 Kian-Meng Ang
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Animate subcommand."""

import argparse
import logging
from contextlib import ExitStack
from pathlib import Path

from fotolab import load_image, open_image

from .common import add_common_arguments, log_args_decorator

log = logging.getLogger(__name__)


def _validate_duration(value: str) -> int:
    """Validate that the duration is a positive integer."""
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(
                f"duration must be a positive integer, but got {value}",
            )
        return ivalue
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"duration must be an integer, but got '{value}'",
        ) from e


def build_subparser(subparsers) -> None:
    """Build the subparser."""
    animate_parser = subparsers.add_parser("animate", help="animate an image")

    animate_parser.set_defaults(func=run)

    add_common_arguments(animate_parser)

    animate_parser.add_argument(
        "-f",
        "--format",
        dest="format",
        type=str,
        choices=["gif", "webp"],
        default="gif",
        help="set the image format (default: '%(default)s')",
        metavar="FORMAT",
    )

    animate_parser.add_argument(
        "-d",
        "--duration",
        dest="duration",
        type=_validate_duration,
        default=2500,
        help=(
            "set the duration in milliseconds "
            "(must be a positive integer, default: '%(default)s')"
        ),
        metavar="DURATION",
    )

    animate_parser.add_argument(
        "-l",
        "--loop",
        dest="loop",
        type=int,
        default=0,
        help="set the loop cycle (default: '%(default)s')",
        metavar="LOOP",
    )

    animate_parser.add_argument(
        "--webp-quality",
        dest="webp_quality",
        type=int,
        default=80,
        choices=range(101),
        help="set WEBP quality (0-100, default: '%(default)s')",
        metavar="QUALITY",
    )

    animate_parser.add_argument(
        "--webp-lossless",
        dest="webp_lossless",
        default=False,
        action="store_true",
        help="enable WEBP lossless compression (default: '%(default)s')",
    )

    animate_parser.add_argument(
        "--webp-method",
        dest="webp_method",
        type=int,
        default=4,
        choices=range(7),
        help=(
            "set WEBP encoding method "
            "(0=fast, 6=slow/best, default: '%(default)s')"
        ),
        metavar="METHOD",
    )

    animate_parser.add_argument(
        "-of",
        "--output-filename",
        dest="output_filename",
        default=None,
        help="set output filename (default: '%(default)s')",
    )


@log_args_decorator
def run(args: argparse.Namespace) -> None:
    """Run animate subcommand.

    Args:
        args (argparse.Namespace): Config from command line arguments

    Returns:
        None
    """
    image_filepaths = [Path(f) for f in args.image_paths]
    first_image_filepath = image_filepaths[0]
    other_frames = []

    with ExitStack() as stack:
        main_frame = stack.enter_context(load_image(first_image_filepath))

        for image_filepath in image_filepaths[1:]:
            img = stack.enter_context(load_image(image_filepath))
            other_frames.append(img)

        if args.output_filename:
            new_filename = Path(args.output_dir, args.output_filename)
        else:
            image_file = Path(first_image_filepath)
            new_filename = Path(
                args.output_dir,
                image_file.with_name(
                    f"animate_{image_file.stem}.{args.format}",
                ),
            )
        new_filename.parent.mkdir(parents=True, exist_ok=True)

        log.info("animate image: %s", new_filename)

        save_kwargs = {
            "format": args.format,
            "append_images": other_frames,
            "save_all": True,
            "duration": args.duration,
            "loop": args.loop,
        }

        # Pillow's WEBP save doesn't use a general 'optimize' like GIF.
        # Specific WEBP params like 'method' and 'quality' control this.
        # 'optimize' is removed for WEBP to avoid confusion.
        if args.format == "gif":
            save_kwargs["optimize"] = True
        elif args.format == "webp":
            save_kwargs["quality"] = args.webp_quality
            save_kwargs["lossless"] = args.webp_lossless
            save_kwargs["method"] = args.webp_method

        main_frame.save(new_filename, **save_kwargs)

    if args.open:
        open_image(new_filename)
