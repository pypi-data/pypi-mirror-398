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


@pytest.mark.parametrize("option", ["-d", "--debug"])
def test_debug_logs(cli_runner, csv_file, option):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv, option)
    assert "debug=True" in ret.stderr
    assert "DEBUG: multiprocessing: number of cpu:" in ret.stderr
    assert "DEBUG: multiprocessing: added worker" in ret.stderr
    assert "generate heatmap:" in ret.stderr


def test_no_debug_logs_in_subprocess(cli_runner, csv_file):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv)
    assert "debug=False" not in ret.stderr
    assert "child process" not in ret.stderr
    assert "process" not in ret.stderr
    assert "generate heatmap:" in ret.stderr


def test_info_logs_format(cli_runner, csv_file):
    csv = csv_file("sample.csv")
    ret = cli_runner(csv)

    log_line = next(
        (
            line
            for line in ret.stderr.splitlines()
            if "generate heatmap:" in line
        ),
        None,
    )

    assert log_line is not None
    assert not log_line.startswith("[")
    assert "INFO" not in log_line
    assert "DEBUG" not in log_line
