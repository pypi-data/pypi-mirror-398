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

"""Resize subcommand."""

import argparse
import logging
import math
from pathlib import Path

from PIL import Image, ImageColor

from fotolab import load_image, save_image

from .common import add_common_arguments, log_args_decorator

log = logging.getLogger(__name__)


def _parse_aspect_ratio(ratio_str: str) -> float:
    """Parse an aspect ratio string (e.g., '16:9') into a float."""
    try:
        width, height = map(int, ratio_str.split(":"))
        if height == 0:
            raise SystemExit("error: height cannot be zero in aspect ratio.")
        return width / height
    except ValueError:
        raise SystemExit(f"error: invalid aspect ratio format: {ratio_str}")


DEFAULT_WIDTH = 600
DEFAULT_HEIGHT = 277


def build_subparser(subparsers) -> None:
    """Build the subparser."""
    resize_parser = subparsers.add_parser("resize", help="resize an image")

    resize_parser.set_defaults(func=run)

    add_common_arguments(resize_parser)

    resize_parser.add_argument(
        "-c",
        "--canvas",
        default=False,
        action="store_true",
        dest="canvas",
        help="paste image onto a larger canvas",
    )

    resize_parser.add_argument(
        "-l",
        "--canvas-color",
        default="black",
        dest="canvas_color",
        help=(
            "the color of the extended larger canvas(default: '%(default)s')"
        ),
    )

    # Define width and height arguments as optional with defaults.
    # The conditional logic (required/mutually exclusive) is now handled in the
    # run function.
    resize_parser.add_argument(
        "-W",
        "--width",
        dest="width",
        help="set the width of the image (default: '%(default)s')",
        type=int,
        default=DEFAULT_WIDTH,
        metavar="WIDTH",
    )

    resize_parser.add_argument(
        "-H",
        "--height",
        dest="height",
        help="set the height of the image (default: '%(default)s')",
        type=int,
        default=DEFAULT_HEIGHT,
        metavar="HEIGHT",
    )

    resize_parser.add_argument(
        "-ar",
        "--aspect-ratio",
        dest="aspect_ratio",
        help="set the aspect ratio of the image (e.g., '16:9', '4:3')",
        type=str,
        default=None,
        metavar="ASPECT_RATIO",
    )


@log_args_decorator
def run(args: argparse.Namespace) -> None:
    """Run resize subcommand.

    Args:
        args (argparse.Namespace): Config from command line arguments

    Returns:
        None
    """
    width_provided = args.width != DEFAULT_WIDTH
    height_provided = args.height != DEFAULT_HEIGHT
    ratio_provided = args.aspect_ratio is not None

    aspect_ratio = None

    if args.canvas:
        # Canvas mode: Both width and height are required
        if not (width_provided and height_provided):
            raise SystemExit(
                "error: argument -W/--width and -H/--height are required when "
                "using --canvas",
            )
        if ratio_provided:
            log.warning(
                "warning: argument -ar/--aspect-ratio is ignored "
                "when using --canvas",
            )
    else:
        # Resize mode:
        if width_provided and height_provided:
            raise SystemExit(
                "error: argument -W/--width and -H/--height are mutually "
                "exclusive when not using --canvas",
            )

        if ratio_provided:
            if not (width_provided or height_provided):
                raise SystemExit(
                    "error: argument -ar/--aspect-ratio requires either "
                    "-W/--width or -H/--height",
                )
            aspect_ratio = _parse_aspect_ratio(args.aspect_ratio)

    for image_filepath in [Path(f) for f in args.image_paths]:
        with load_image(image_filepath) as original_image:
            if args.canvas:
                resized_image = _resize_image_onto_canvas(original_image, args)
            else:
                resized_image = _resize_image(
                    original_image,
                    args,
                    aspect_ratio,
                )
            save_image(args, resized_image, image_filepath, "resize")


def _resize_image_onto_canvas(original_image, args):
    resized_image = Image.new(
        "RGB",
        (args.width, args.height),
        (*ImageColor.getrgb(args.canvas_color), 128),
    )
    x_offset = (args.width - original_image.width) // 2
    y_offset = (args.height - original_image.height) // 2
    resized_image.paste(original_image, (x_offset, y_offset))
    return resized_image


def _resize_image(original_image, args, aspect_ratio):
    new_width, new_height = _calc_new_image_dimension(
        original_image,
        args,
        aspect_ratio,
    )
    resized_image = original_image.copy()
    resized_image = resized_image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS,
    )
    return resized_image


def _calc_new_image_dimension(image, args, aspect_ratio) -> tuple:
    old_width, old_height = image.size
    log.debug("old image dimension: %d x %d", old_width, old_height)

    new_width = args.width
    new_height = args.height

    # Determine the aspect ratio to use for calculation
    if aspect_ratio is not None:
        ratio_to_use = aspect_ratio
        log.debug("using specified aspect ratio: %f", ratio_to_use)
    else:
        ratio_to_use = old_width / old_height
        log.debug("using original aspect ratio: %f", ratio_to_use)

    width_provided = new_width != DEFAULT_WIDTH
    height_provided = new_height != DEFAULT_HEIGHT

    match (width_provided, height_provided):
        case (True, False):
            # user provided width, calculate height
            new_height = math.ceil(new_width / ratio_to_use)
            log.debug("new height calculated based on width: %d", new_height)
        case (False, True):
            # user provided height, calculate width
            new_width = math.ceil(new_height * ratio_to_use)
            log.debug("new width calculated based on height: %d", new_width)
        case _:
            # if both are default, no calculation needed, use defaults
            # the case where both are non-default is disallowed by validation
            # in run()
            pass

    log.debug("new image dimension: %d x %d", new_width, new_height)
    return (new_width, new_height)
