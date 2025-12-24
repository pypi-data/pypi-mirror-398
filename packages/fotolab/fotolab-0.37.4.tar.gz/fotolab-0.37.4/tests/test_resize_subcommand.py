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


def test_resize_subcommand(cli_runner, image_file):
    img_path = image_file("sample.png")
    ret = cli_runner("resize", str(img_path), "--width", "200")
    assert ret.returncode == 0


def test_resize_subcommand_aspect_ratio_success(cli_runner, image_file):
    img_path = image_file("sample.png")
    ret = cli_runner(
        "resize",
        str(img_path),
        "--width",
        "320",
        "--aspect-ratio",
        "16:9",
    )
    assert ret.returncode == 0


def test_resize_subcommand_aspect_ratio_missing_dimension_failure(
    cli_runner,
    image_file,
):
    img_path = image_file("sample.png")
    ret = cli_runner("resize", str(img_path), "--aspect-ratio", "16:9")
    assert ret.returncode != 0
    assert (
        "error: argument -ar/--aspect-ratio requires "
        "either -W/--width or -H/--height" in ret.stderr
    )


def test_resize_subcommand_mutually_exclusive_failure(cli_runner, image_file):
    img_path = image_file("sample.png")
    ret = cli_runner(
        "resize",
        str(img_path),
        "--width",
        "200",
        "--height",
        "200",
    )
    assert ret.returncode != 0
    assert (
        "error: argument -W/--width and -H/--height are mutually "
        "exclusive when not using --canvas" in ret.stderr
    )


def test_resize_subcommand_canvas_required_failure(cli_runner, image_file):
    img_path = image_file("sample.png")
    ret = cli_runner("resize", str(img_path), "--canvas", "--width", "200")
    assert ret.returncode != 0
    assert (
        "error: argument -W/--width and -H/--height are "
        "required when using --canvas" in ret.stderr
    )

    ret = cli_runner("resize", str(img_path), "--canvas", "--height", "200")
    assert ret.returncode != 0
    assert (
        "error: argument -W/--width and -H/--height are "
        "required when using --canvas" in ret.stderr
    )


def test_resize_subcommand_canvas_success(cli_runner, image_file):
    img_path = image_file("sample.png")
    ret = cli_runner(
        "resize",
        str(img_path),
        "--canvas",
        "--width",
        "200",
        "--height",
        "200",
    )
    assert ret.returncode == 0
