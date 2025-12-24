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

from pathlib import Path

import pytest


@pytest.mark.parametrize("option", ["-y", "--year"])
def test_debug_logs(cli_runner, csv_file, option):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "-d", option, "2023")
    assert "year=2023" in ret.stderr


def test_raise_exception_no_data_from_csv(cli_runner, csv_file):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "-y", "2099")
    assert (
        "error: No data extracted from CSV file for the specified period!"
        in ret.stderr
    )


def test_multiple_years_generates_multiple_files(cli_runner, csv_file, tmpdir):
    csv = csv_file("sample.csv")
    years = ["2023", "2024"]
    args = ["-y", years[0], "-y", years[1]]
    ret = cli_runner(csv, *args)

    assert ret.returncode == 0, ret.stderr

    output_dir = Path(str(tmpdir.join("scripttest", "output")))
    output_files = [f for f in output_dir.glob("*.png")]

    assert len(output_files) == len(years), (
        f"Expected {len(years)} files in output directory, found {len(output_files)}. "
        f"Files found: {output_files}"
    )

    year_in_file = [
        any(str(year) in str(f) for year in years) for f in output_files
    ]
    assert len(year_in_file) == len(output_files) and all(year_in_file)
