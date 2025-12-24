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

"""Crop subcommand."""

import argparse
import logging
from pathlib import Path

from fotolab import load_image, save_image

from .common import add_common_arguments, log_args_decorator

log = logging.getLogger(__name__)


def build_subparser(subparsers) -> None:
    """Build the subparser."""
    crop_parser = subparsers.add_parser("crop", help="crop an image")

    crop_parser.set_defaults(func=run)

    add_common_arguments(crop_parser)

    crop_parser.add_argument(
        "-b",
        "--box",
        dest="box",
        help=(
            "set the crop area as a 4-tuple (left, upper, right, lower), "
            "e.g., '100,100,500,500'"
        ),
        type=str,
        required=True,
        metavar="BOX",
    )


def _parse_box(box_str: str) -> tuple[int, int, int, int]:
    """Parse a box string (e.g., '100,100,500,500') into a 4-tuple of
    integers.
    """
    try:
        parts = list(map(int, box_str.split(",")))
        if len(parts) != 4:
            raise ValueError(
                "Box must contain exactly four comma-separated integers.",
            )
        left, upper, right, lower = parts
        if left < 0 or upper < 0 or right < 0 or lower < 0:
            raise ValueError("All coordinates must be non-negative.")
        if left >= right or upper >= lower:
            raise ValueError(
                "Left coordinate must be less than right, "
                "and upper must be less than lower.",
            )
        return (left, upper, right, lower)
    except ValueError as e:
        raise SystemExit(f"error: invalid box format: {box_str}. {e}")


@log_args_decorator
def run(args: argparse.Namespace) -> None:
    """Run crop subcommand.

    Args:
        args (argparse.Namespace): Config from command line arguments

    Returns:
        None
    """
    crop_box = _parse_box(args.box)

    for image_filepath in [Path(f) for f in args.image_paths]:
        with load_image(image_filepath) as original_image:
            log.debug("Original image size: %s", original_image.size)

            # Check if the crop box is within the image boundaries
            img_width, img_height = original_image.size
            left, upper, right, lower = crop_box

            if right > img_width or lower > img_height:
                log.warning(
                    "Crop box (%s) extends beyond image boundaries (%d, %d). "
                    "Cropping to the maximum possible area.",
                    args.box,
                    img_width,
                    img_height,
                )
                # Adjust the box to fit within the image
                right = min(right, img_width)
                lower = min(lower, img_height)
                crop_box = (left, upper, right, lower)

            if left >= right or upper >= lower:
                log.error(
                    "Adjusted crop box (%s) is invalid or results in "
                    "zero area. Skipping image.",
                    crop_box,
                )
                continue

            cropped_image = original_image.crop(crop_box)
            log.debug("Cropped image size: %s", cropped_image.size)

            save_image(args, cropped_image, image_filepath, "crop")
