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


def test_default_value_for_option_in_help(script_runner):
    ret = script_runner("xstxt", "-h")

    expects = [
        "set css path of chapter title (default: 'title')",
        "set css path of chapter body (default: 'body')",
        "set title of the novel (default: '不详')",
        "set author of the novel (default: '不详')",
        "set glob pattern of html files to process (default: '['./*.html']')",
        "set glob pattern of html files to exclude (default: '[]')",
        "set number of html files to process (default: '3')",
        "set output txt file name (default: 'book.txt')",
        "generate config file from options (default: 'xstxt.toml')",
        "load config from file (default: 'xstxt.toml')",
        "load config from file (default: 'xstxt.toml')",
        "set css path of chapter title (default: 'title')",
        "set css path of chapter body (default: 'body')",
        "set title of the novel (default: '不详')",
        "set author of the novel (default: '不详')",
        "set glob pattern of html files to process (default: '['./*.html']')",
        "set glob pattern of html files to exclude (default: '[]')",
        "set number of html files to process (default: '3')",
        "set output txt file name (default: 'book.txt')",
        "generate config file from options (default: 'xstxt.toml')",
        "load config from file (default: 'xstxt.toml')",
    ]

    for expect in expects:
        assert expect in ret.stdout
