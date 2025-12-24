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

"""Black and white subcommand."""

import argparse
import logging

from PIL import Image, ImageEnhance

from .common import (
    add_common_arguments,
    log_args_decorator,
    process_images_in_batches,
)

log = logging.getLogger(__name__)

FILTER_SETTINGS = {
    # 1. High Contrast, Deep Blacks. (A strong S-curve simulation)
    "DEEP_BLACK": {
        "contrast_factor": 1.5,
        "brightness_factor": 0.9,
        "sharpen_factor": 1.2,
    },
    # 2. Softer Contrast, Balanced Mid-tones. (Closer to a simple greyscale)
    "TRUE_GRAY": {
        "contrast_factor": 1.1,
        "brightness_factor": 1.05,
        "sharpen_factor": 1.0,
    },
    # 3. Soft Contrast, Flattering and Smooth. (Muted highlights and smooth
    # transitions)
    "SOFT_LIGHT": {
        "contrast_factor": 1.3,
        "brightness_factor": 1.1,
        "sharpen_factor": 0.9,
    },
    # 4. Very high contrast, punchy. (Extra clarity and sharpening)
    "GRAIN": {
        "contrast_factor": 1.6,
        "brightness_factor": 1.0,
        "sharpen_factor": 1.5,
    },
}

FILTER_CHOICES = list(FILTER_SETTINGS.keys())


def _apply_bw_enhancements(
    image: Image.Image,
    contrast_factor: float = 1.0,
    brightness_factor: float = 1.0,
    sharpen_factor: float = 1.0,
) -> Image.Image:
    """Converts image to grayscale and applies contrast, brightness, and sharpness
    enhancements based on the provided factors.
    """
    # 1. Convert to Grayscale ('L' mode)
    img = image.convert("L")

    # 2. Apply Contrast
    contraster = ImageEnhance.Contrast(img)
    img = contraster.enhance(contrast_factor)

    # 3. Apply Brightness
    brighter = ImageEnhance.Brightness(img)
    img = brighter.enhance(brightness_factor)

    # 4. Apply Sharpening
    sharper = ImageEnhance.Sharpness(img)
    img = sharper.enhance(sharpen_factor)

    return img


def _apply_bw_filter(image: Image.Image, filter_key: str) -> Image.Image:
    """Applies a predefined black and white filter based on the filter key."""
    settings = FILTER_SETTINGS[filter_key]

    return _apply_bw_enhancements(
        image,
        contrast_factor=settings.get("contrast_factor", 1.0),
        brightness_factor=settings.get("brightness_factor", 1.0),
        sharpen_factor=settings.get("sharpen_factor", 1.0),
    )


def build_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Build the subparser."""
    bw_parser = subparsers.add_parser(
        "bw",
        help="apply a black and white filter effect to an image",
    )

    bw_parser.set_defaults(func=run)

    add_common_arguments(bw_parser)

    group = bw_parser.add_mutually_exclusive_group(required=False)

    group.add_argument(
        "-f",
        "--filter",
        dest="filter_type",
        type=str,
        choices=FILTER_CHOICES,
        help=(
            "specify the black and white filter type to apply, "
            f"choices: {', '.join(FILTER_CHOICES)}"
        ),
        metavar="FILTER_TYPE",
    )

    group.add_argument(
        "--all-filters",
        default=False,
        action="store_true",
        dest="all_filters",
        help="apply all available filters to the image",
    )

    bw_parser.add_argument(
        "--contrast",
        type=float,
        default=None,
        help="apply a custom contrast factor (e.g., 1.5 for 50%% increase)",
    )
    bw_parser.add_argument(
        "--brightness",
        type=float,
        default=None,
        help="apply a custom brightness factor (e.g., 1.1 for 10%% increase)",
    )
    bw_parser.add_argument(
        "--sharpen",
        type=float,
        default=None,
        help="apply a custom sharpen factor (e.g., 2.0 for double sharpening)",
    )


def _handle_custom_enhancements(args: argparse.Namespace) -> None:
    """Handles the application of custom contrast, brightness, and sharpen
    factors.
    """
    # Use 1.0 as default if not provided
    contrast = args.contrast if args.contrast is not None else 1.0
    brightness = args.brightness if args.brightness is not None else 1.0
    sharpen = args.sharpen if args.sharpen is not None else 1.0

    # Create a suffix based on the applied custom options
    suffix_parts = ["bw"]
    if args.contrast is not None:
        suffix_parts.append(f"c{args.contrast:.2f}".replace(".", "_"))
    if args.brightness is not None:
        suffix_parts.append(f"b{args.brightness:.2f}".replace(".", "_"))
    if args.sharpen is not None:
        suffix_parts.append(f"s{args.sharpen:.2f}".replace(".", "_"))
    suffix = "_".join(suffix_parts)

    def custom_processor(
        image: Image.Image,
        args: argparse.Namespace,
    ) -> Image.Image:
        # Factors are calculated once and captured from outer scope
        return _apply_bw_enhancements(
            image,
            contrast_factor=contrast,
            brightness_factor=brightness,
            sharpen_factor=sharpen,
        )

    process_images_in_batches(
        args,
        custom_processor,
        suffix,
        "Applying custom black and white enhancements to %s",
    )


def _handle_filter_application(args: argparse.Namespace) -> None:
    """Handles the application of predefined black and white filters."""
    filters_to_apply = []
    if args.all_filters:
        filters_to_apply = FILTER_CHOICES
    elif args.filter_type:
        filters_to_apply = [args.filter_type]

    # This check should theoretically not be hit if run() is called correctly,
    # but it acts as a safeguard.
    if not filters_to_apply:
        log.error("Internal error: filter application called without filters.")
        raise SystemExit(1)

    for filter_type in filters_to_apply:

        def filter_processor(
            image: Image.Image,
            args: argparse.Namespace,
        ) -> Image.Image:
            # args is ignored here
            return _apply_bw_filter(image, filter_type)

        suffix = f"bw_{filter_type.lower()}"
        log_message = f"Applying black and white filter '{filter_type}' to %s"

        process_images_in_batches(
            args,
            filter_processor,
            suffix,
            log_message,
        )


@log_args_decorator
def run(args: argparse.Namespace) -> None:
    """Run bw subcommand.

    Args:
        args (argparse.Namespace): Config from command line arguments

    Returns:
        None
    """
    is_custom_run = (
        args.contrast is not None
        or args.brightness is not None
        or args.sharpen is not None
    )

    if is_custom_run:
        if args.filter_type or args.all_filters:
            log.warning(
                "Custom enhancement options (--contrast, --brightness, "
                "--sharpen) were provided. Filter options (-f, --all-filters) "
                "will be ignored.",
            )
        _handle_custom_enhancements(args)
    elif args.filter_type or args.all_filters:
        _handle_filter_application(args)
    else:
        log.error(
            "No filter or custom enhancement options provided. "
            "Please use -f, --all-filters, or one of --contrast, "
            "--brightness, or --sharpen.",
        )
        raise SystemExit(1)
