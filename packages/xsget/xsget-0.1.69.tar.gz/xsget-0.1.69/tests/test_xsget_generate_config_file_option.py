# Copyright (C) 2021,2022,2023,2024,2025 Kian-Meng Ang
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# pylint: disable=C0114,C0116

import pytest

DEFAULT_URL = "http://localhost"


def test_generating_default_config_file(script_runner):
    ret = script_runner("xsget", DEFAULT_URL, "-g")
    assert "Create config file: xsget.toml" in ret.stdout
    assert (
        "Cannot connect to host localhost:80 "
        "ssl:default [Connect call failed ('127.0.0.1', 80)]" in ret.stdout
    )


@pytest.mark.skip(reason="TODO")
def test_raise_exception_for_creating_duplicate_config_file(script_runner):
    _ = script_runner("xsget", DEFAULT_URL, "-g")
    ret = script_runner("xsget", DEFAULT_URL, "-g")
    logs = [
        "error: Existing config file found: xsget.toml",
        "xsget.ConfigFileExistsError: Existing config file found: xsget.toml",
    ]
    for log in logs:
        assert log in ret.stdout


@pytest.mark.skip(reason="TODO")
def test_generating_default_config_file_with_existing_found(script_runner):
    _ = script_runner("xsget", DEFAULT_URL, "-g")
    ret = script_runner("xsget", DEFAULT_URL, "-g")
    assert "Existing config file found: xsget.toml" in ret.stdout
