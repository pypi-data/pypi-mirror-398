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


@pytest.mark.parametrize("option", ["-w", "--week"])
def test_debug_logs(cli_runner, csv_file, option):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "-y", "2024", "-d", option, "42")

    assert "week=42" in ret.stderr


def test_last_week_of_the_year(cli_runner, csv_file):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "-y", "2024", "-d", "-w", "52")

    assert "week=52" in ret.stderr


def test_end_date_option_valid(cli_runner, csv_file):
    """Test that --end-date correctly sets year and week."""
    csv = csv_file("sample.csv")
    # 2025-10-25 is in week 43 of 2025 (ISO calendar)
    ret = cli_runner(csv, "-d", "--end-date", "2025-10-25")

    assert "year=2025" in ret.stderr
    assert "week=43" in ret.stderr


def test_end_date_option_invalid_format(cli_runner, csv_file):
    """Test that --end-date raises an error for an invalid date format."""
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "--end-date", "2025-13-01", expect_error=True)

    assert ret.returncode == 2
    assert (
        "invalid date format: '2025-13-01', expected YYYY-MM-DD." in ret.stderr
    )
