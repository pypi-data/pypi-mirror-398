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

"""Rotate subcommand."""

import argparse
import logging
from pathlib import Path

from PIL import Image

from fotolab import load_image, save_image

from .common import add_common_arguments, log_args_decorator

log = logging.getLogger(__name__)


def build_subparser(subparsers) -> None:
    """Build the subparser."""
    rotate_parser = subparsers.add_parser("rotate", help="rotate an image")

    rotate_parser.set_defaults(func=run)

    add_common_arguments(rotate_parser)

    rotate_parser.add_argument(
        "-r",
        "--rotation",
        type=int,
        default=0,
        help="Rotation angle in degrees (default: '%(default)s')",
    )

    rotate_parser.add_argument(
        "-cw",
        "--clockwise",
        action="store_true",
        help="Rotate clockwise (default: '%(default)s)",
    )


@log_args_decorator
def run(args: argparse.Namespace) -> None:
    """Run rotate subcommand.

    Args:
        args (argparse.Namespace): Config from command line arguments

    Returns:
        None
    """
    rotation = -args.rotation if args.clockwise else args.rotation
    log.debug(f"Rotation angle: {rotation} degrees")

    for image_path_str in args.image_paths:
        image_filename = Path(image_path_str)
        log.debug(f"Processing image: {image_filename}")
        with load_image(image_filename) as original_image:
            log.debug(f"Original image size: {original_image.size}")
            rotated_image = original_image.rotate(
                rotation,
                expand=True,
                resample=Image.Resampling.BICUBIC,
            )
            log.debug(f"Rotated image size: {rotated_image.size}")
            save_image(args, rotated_image, image_filename, "rotate")
            log.debug(f"Image saved: {image_filename}")
