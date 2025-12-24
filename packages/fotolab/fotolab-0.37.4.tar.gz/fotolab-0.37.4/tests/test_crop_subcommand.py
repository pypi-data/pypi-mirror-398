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


def test_crop_subcommand_success(cli_runner, image_file, tmpdir):
    img_path = image_file("sample.png")

    ret = cli_runner(
        "--overwrite",
        "crop",
        str(img_path),
        "--box",
        "50,50,150,150",
        "--output-dir",
        ".",
    )
    assert ret.returncode == 0


def test_crop_subcommand_missing_box_failure(cli_runner, image_file):
    img_path = image_file("sample.png")
    ret = cli_runner("crop", str(img_path))
    assert ret.returncode != 0
    assert (
        "error: the following arguments are required: -b/--box" in ret.stderr
    )


def test_crop_subcommand_invalid_box_format_failure(cli_runner, image_file):
    img_path = image_file("sample.png")
    ret = cli_runner("crop", str(img_path), "--box", "10,10,100")
    assert ret.returncode != 0
    assert (
        "error: invalid box format: 10,10,100. "
        "Box must contain exactly four comma-separated integers." in ret.stderr
    )

    ret = cli_runner("crop", str(img_path), "--box", "10,10,100,abc")
    assert ret.returncode != 0
    assert (
        "error: invalid box format: 10,10,100,abc. invalid literal for int()"
        in ret.stderr
    )


def test_crop_subcommand_invalid_coordinates_failure(cli_runner, image_file):
    img_path = image_file("sample.png")
    # left >= right
    ret = cli_runner("crop", str(img_path), "--box", "100,100,50,200")
    assert ret.returncode != 0
    assert (
        "error: invalid box format: 100,100,50,200. "
        "Left coordinate must be less than right, and "
        "upper must be less than lower." in ret.stderr
    )

    # upper >= lower
    ret = cli_runner("crop", str(img_path), "--box", "50,200,100,100")
    assert ret.returncode != 0
    assert (
        "error: invalid box format: 50,200,100,100. "
        "Left coordinate must be less than right, and "
        "upper must be less than lower." in ret.stderr
    )
