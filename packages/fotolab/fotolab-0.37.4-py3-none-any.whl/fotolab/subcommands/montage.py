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

"""Montage subcommand."""

import argparse
import logging
from contextlib import ExitStack
from pathlib import Path

from PIL import Image

from fotolab import load_image, save_image

from .common import add_common_arguments, log_args_decorator

log = logging.getLogger(__name__)


def build_subparser(subparsers) -> None:
    """Build the subparser."""
    montage_parser = subparsers.add_parser(
        "montage",
        help="montage a list of image",
    )

    montage_parser.set_defaults(func=run)

    add_common_arguments(montage_parser)


@log_args_decorator
def run(args: argparse.Namespace) -> None:
    """Run montage subcommand.

    Args:
        args (argparse.Namespace): Config from command line arguments

    Returns:
        None
    """
    images = []
    with ExitStack() as stack:
        for image_path_str in args.image_paths:
            image_filename = Path(image_path_str)
            images.append(stack.enter_context(load_image(image_filename)))

        if len(images) < 2:
            raise ValueError("at least two images is required for montage")

        total_width = sum(img.width for img in images)
        total_height = max(img.height for img in images)

        montaged_image = Image.new("RGB", (total_width, total_height))

        x_offset = 0
        for image in images:
            montaged_image.paste(image, (x_offset, 0))
            x_offset += image.width

        output_image_filename = Path(args.image_paths[0])
        save_image(args, montaged_image, output_image_filename, "montage")
