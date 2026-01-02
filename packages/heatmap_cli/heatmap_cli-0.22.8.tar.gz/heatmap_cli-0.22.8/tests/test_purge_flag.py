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


@pytest.mark.parametrize("option", ["-p", "--purge"])
def test_debug_logs(cli_runner, csv_file, option):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, "-y", "2024", "-d", option)

    assert "purge=True" in ret.stderr


def test_purge_output_folder_if_exists(cli_runner, csv_file, tmpdir):
    csv = csv_file("sample.csv")
    opf = f"{tmpdir}/output"

    _ = cli_runner(csv, "-y", "2024", "-d", "-O", opf, "-w", "42")
    ret = cli_runner(
        csv,
        "-y",
        "2024",
        "-v",
        "-O",
        opf,
        "-p",
        "-Y",
        "-w",
        "42",
    )

    assert f"Purging output folder: {opf}" in ret.stderr


def test_prompt_when_purging_output_folder(cli_runner, csv_file, tmpdir):
    csv = csv_file("sample.csv")
    opf = f"{tmpdir}/output"

    _ = cli_runner(csv, "-y", "2024", "-d", "-O", opf, "-w", "42")
    ret = cli_runner(csv, "-y", "2024", "-d", "-O", opf, "-p", stdin=b"y")

    assert f"Are you sure to purge output folder: {opf}? [y/N] " in ret.stdout


def test_no_purge_output_folder_if_not_exists(cli_runner, csv_file):
    csv = csv_file("sample.csv")
    output_folder = csv.resolve().parent.joinpath("output")
    ret = cli_runner(csv, "-y", "2024", "-d", "-p")

    assert f"purge output folder: {output_folder}" not in ret.stdout
