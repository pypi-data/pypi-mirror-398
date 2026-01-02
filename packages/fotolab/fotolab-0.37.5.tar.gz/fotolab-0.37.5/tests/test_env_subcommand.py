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

import platform
import sys

from fotolab import __version__


def test_env_output(cli_runner):
    ret = cli_runner("env")

    actual_sys_version = sys.version.replace("\n", "")
    actual_platform = platform.platform()

    expected_output = (
        f"fotolab: {__version__}\n"
        f"python: {actual_sys_version}\n"
        f"platform: {actual_platform}\n"
    )

    assert ret.stdout == expected_output
    assert ret.stderr == ""
    assert ret.returncode == 0
