# Copyright (C) 2023,2024,2025 Kian-Meng Ang
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pytest


@pytest.mark.parametrize("option", ["-c", "--cmap"])
def test_debug_logs(cli_runner, csv_file, option):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "-d", option, "autumn")
    assert "cmap=['autumn']" in ret.stderr


def test_default_cmap(cli_runner, csv_file):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "-d")
    assert "cmap=['RdYlGn_r']" in ret.stderr


def test_cmap_help_message(cli_runner):
    ret = cli_runner("--help")
    assert "Set default colormap." in ret.stdout
    assert "Available colormaps:" in ret.stdout
    assert "viridis" in ret.stdout
    assert "plasma" in ret.stdout


@pytest.mark.parametrize("option", ["-c", "--cmap"])
def test_multiple_cmaps(cli_runner, csv_file, option):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "-d", option, "autumn", option, "RdYlGn_r")
    assert "cmap=['autumn', 'RdYlGn_r']" in ret.stderr
