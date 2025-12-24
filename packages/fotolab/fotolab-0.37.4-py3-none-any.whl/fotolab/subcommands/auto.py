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

"""Auto subcommand."""

import argparse
import logging

import fotolab.subcommands.animate
import fotolab.subcommands.contrast
import fotolab.subcommands.resize
import fotolab.subcommands.sharpen
import fotolab.subcommands.watermark

from .common import add_common_arguments, log_args_decorator

log = logging.getLogger(__name__)


def build_subparser(subparsers) -> None:
    """Build the subparser."""
    auto_parser = subparsers.add_parser(
        "auto",
        help="auto adjust (resize, contrast, and watermark) a photo",
    )

    auto_parser.set_defaults(func=run)

    add_common_arguments(auto_parser)

    auto_parser.add_argument(
        "-t",
        "--title",
        dest="title",
        help="set the tile (default: '%(default)s')",
        type=str,
        default=None,
        metavar="TITLE",
    )

    auto_parser.add_argument(
        "-w",
        "--watermark",
        dest="watermark",
        help="set the watermark (default: '%(default)s')",
        type=str,
        default="kianmeng.org",
        metavar="WATERMARK_TEXT",
    )


@log_args_decorator
def run(args: argparse.Namespace) -> None:
    """Run auto subcommand.

    Args:
        args (argparse.Namespace): Config from command line arguments

    Returns:
        None
    """
    text = args.watermark
    if args.title and args.watermark:
        text = f"{args.title}\n{args.watermark}"

    extra_args = {
        "width": 600,
        "height": 277,
        "cutoff": 1,
        "radius": 1,
        "percent": 100,
        "threshold": 2,
        "text": text,
        "position": "bottom-left",
        "font_size": 12,
        "font_color": "white",
        "outline_width": 2,
        "outline_color": "black",
        "padding": 15,
        "padding_x": None,
        "padding_y": None,
        "camera": False,
        "canvas": False,
        "lowercase": True,
        "before_after": False,
        "alpha": 128,
        "aspect_ratio": None,
    }

    # resolve error: argparse.Namespace() got multiple values for keyword
    # argument 'text'
    merged_args = {**vars(args), **extra_args}
    combined_args = argparse.Namespace(**merged_args)
    combined_args.overwrite = True
    combined_args.open = False

    log.debug(combined_args)

    fotolab.subcommands.resize.run(combined_args)
    fotolab.subcommands.contrast.run(combined_args)
    fotolab.subcommands.sharpen.run(combined_args)
    fotolab.subcommands.watermark.run(combined_args)

    if len(args.image_paths) > 1:
        output_filename = (
            args.title.lower().replace(",", "").replace(" ", "_") + ".gif"
        )
        combined_args.format = "gif"
        combined_args.duration = 2500
        combined_args.loop = 0
        combined_args.output_filename = output_filename
        fotolab.subcommands.animate.run(combined_args)
