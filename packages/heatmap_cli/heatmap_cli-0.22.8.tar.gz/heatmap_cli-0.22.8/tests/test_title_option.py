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


@pytest.mark.parametrize("option", ["-t", "--title"])
def test_debug_logs(cli_runner, csv_file, option):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "-y", "2024", "-d", option, "my title is foobar")
    assert "title='my title is foobar'" in ret.stderr
    assert "my title is foobar" in ret.stderr


def test_default_title(cli_runner, csv_file):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "-y", "2024", "-d", "-w", "42")
    assert "Year 2024: Total Daily Walking Steps Through Week 42" in ret.stderr


def test_default_title_on_last_week_of_the_year(cli_runner, csv_file):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "-y", "2024", "-d", "-w", "52")
    assert "Year 2024: Total Daily Walking Steps" in ret.stderr
