# Copyright (C) 2024,2025 Kian-Meng Ang

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

from pathlib import Path

from PIL import Image


def test_watermark_subcommand(cli_runner, image_file):
    img_path = image_file("sample.png")
    ret = cli_runner("watermark", str(img_path), "--text", "Test")
    assert ret.returncode == 0


def test_watermark_color_mode_rgb_to_rgba_to_rgb_conversion(
    cli_runner,
    image_file,
):
    img_path = image_file("rgb_sample.jpg")

    output_dir = Path("output")
    ret = cli_runner(
        "watermark",
        str(img_path),
        "--output-dir",
        str(output_dir),
        "--text",
        "Test",
    )
    assert ret.returncode == 0

    output_filename = (
        Path("scripttest")
        / output_dir
        / f"watermark_{img_path.stem}{img_path.suffix}"
    )

    with Image.open(output_filename) as image:
        assert image.mode == "RGB"
