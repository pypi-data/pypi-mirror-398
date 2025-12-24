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

"""Halftone subcommand."""

import argparse
import logging
import math
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageDraw

from fotolab import load_image, save_gif_image, save_image

from .common import add_common_arguments, log_args_decorator

log = logging.getLogger(__name__)


class HalftoneCell(NamedTuple):
    """Represents a cell in the halftone grid."""

    col: int
    row: int
    cellsize: float


def build_subparser(subparsers) -> None:
    """Build the subparser."""
    halftone_parser = subparsers.add_parser(
        "halftone",
        help="halftone an image",
    )

    halftone_parser.set_defaults(func=run)

    add_common_arguments(halftone_parser)

    halftone_parser.add_argument(
        "-ba",
        "--before-after",
        default=False,
        action="store_true",
        dest="before_after",
        help="generate a GIF showing before and after changes",
    )

    halftone_parser.add_argument(
        "-c",
        "--cells",
        dest="cells",
        type=int,
        default=50,
        help=(
            "set number of cells across the image width (default: %(default)s)"
        ),
    )

    halftone_parser.add_argument(
        "-g",
        "--grayscale",
        default=False,
        action="store_true",
        dest="grayscale",
        help="convert image to grayscale before applying halftone",
    )


@log_args_decorator
def run(args: argparse.Namespace) -> None:
    """Run halftone subcommand.

    Args:
        args (argparse.Namespace): Config from command line arguments

    Returns:
        None
    """
    for image_path_str in args.image_paths:
        image_filename = Path(image_path_str)
        with load_image(image_filename) as original_image:
            halftone_image = create_halftone_image(
                original_image,
                args.cells,
                args.grayscale,
            )

            if args.before_after:
                save_gif_image(
                    args,
                    image_filename,
                    original_image,
                    halftone_image,
                    "halftone",
                )
            else:
                save_image(args, halftone_image, image_filename, "halftone")


def _draw_halftone_dot(
    draw: ImageDraw.ImageDraw,
    source_image: Image.Image,
    brightness_map: Image.Image,
    cell: HalftoneCell,
    grayscale: bool,
    fill_color_dot: int,
) -> None:
    """Calculate properties and draw a single halftone dot."""
    # calculate center point of current cell
    img_width, img_height = source_image.size

    # calculate center point of current cell and clamp to image bounds
    x = min(int(cell.col * cell.cellsize + cell.cellsize / 2), img_width - 1)
    y = min(int(cell.row * cell.cellsize + cell.cellsize / 2), img_height - 1)

    # ensure coordinates are non-negative (shouldn't happen with current logic,
    # but safe)
    x = max(0, x)
    y = max(0, y)

    # Get brightness from the pre-calculated map (L mode)
    brightness = brightness_map.getpixel((x, y))

    # Get pixel value (color) from the source image
    pixel_value = source_image.getpixel((x, y))

    if grayscale:
        # In grayscale mode, source_image is L mode, pixel_value is brightness
        # dot_fill is the fixed color (255 for white dot on black background)
        dot_fill = fill_color_dot
    else:
        # In color mode, dot_fill is the original color
        dot_fill = pixel_value

    # calculate dot radius relative to cell size based on brightness max radius
    # is half the cell size
    # scale by brightness (0-255).
    dot_radius = (brightness / 255.0) * (cell.cellsize / 2)

    # draw the dot
    draw.ellipse(
        [
            x - dot_radius,
            y - dot_radius,
            x + dot_radius,
            y + dot_radius,
        ],
        fill=dot_fill,
    )


def create_halftone_image(
    original_image: Image.Image,
    cell_count: int,
    grayscale: bool = False,
) -> Image.Image:
    """Create a halftone version of the input image.

    Modified from the circular halftone effect processing.py example from
    https://tabreturn.github.io/code/processing/python/2019/02/09/processing.py_in_ten_lessons-6.3-_halftones.html

    Args:
        original_image: The source image to convert
        cell_count: Number of cells across the width
        grayscale: Whether to convert to grayscale first (default: False)

    Returns:
        Image.Image: The halftone converted image
    """
    output_mode: str
    fill_color_black: int | tuple[int, int, int]
    fill_color_dot_for_grayscale: int

    # Always create a grayscale version for brightness calculation (dot size)
    brightness_map = original_image.convert("L")

    if grayscale:
        source_image = brightness_map
        output_mode = "L"
        fill_color_black = 0
        fill_color_dot_for_grayscale = 255
    else:
        source_image = original_image.convert("RGB")
        output_mode = "RGB"
        fill_color_black = (0, 0, 0)
        fill_color_dot_for_grayscale = 0

    width, height = original_image.size

    # create a new image for the output, initialized to black
    halftone_image = Image.new(output_mode, (width, height), fill_color_black)
    draw = ImageDraw.Draw(halftone_image)

    cellsize = width / cell_count
    rowtotal = math.ceil(height / cellsize)

    for row in range(rowtotal):
        for col in range(cell_count):
            cell = HalftoneCell(col=col, row=row, cellsize=cellsize)
            _draw_halftone_dot(
                draw,
                source_image,
                brightness_map,
                cell,
                grayscale,
                fill_color_dot_for_grayscale,
            )

    return halftone_image
