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


@pytest.mark.parametrize("option", ["-e", "--end-date"])
def test_debug_logs(cli_runner, csv_file, option):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "-d", option, "2023-01-01")
    assert "end_date='2023-01-01'" in ret.stderr


def test_raise_exception_no_data_from_csv(cli_runner, csv_file):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "-e", "1999-01-01")
    assert (
        "error: No data extracted from CSV file for the specified period!"
        in ret.stderr
    )


@pytest.mark.parametrize("option", ["-e", "--end-date"])
def test_raise_exception_invalid_date_format(cli_runner, csv_file, option):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, option, "01-01-2023")
    assert (
        "argument --end-date: invalid date format: '01-01-2023', expected YYYY-MM-DD."
        in ret.stderr
    )
