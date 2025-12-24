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


def test_montage_subcommand(cli_runner, image_file):
    img_path = image_file("sample.png")
    ret = cli_runner("montage", str(img_path), str(img_path))
    assert ret.returncode == 0


def test_montage_subcommand_with_single_image_raises_error(
    cli_runner,
    image_file,
):
    img_path = image_file("sample.png")
    ret = cli_runner("montage", str(img_path))
    assert ret.returncode != 0
    assert "error: at least two images is required for montage" in ret.stdout
