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

"""Shared argument parsing for xsget and xstxt."""

import argparse
import platform
import sys
from collections.abc import Sequence
from typing import Any

from xsget import __version__


class EnvironmentAction(argparse.Action):
    """Show environment details action."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the EnvironmentAction."""
        kwargs["nargs"] = 0
        super().__init__(**kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        _namespace: argparse.Namespace,
        _values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        """Print environment details and exit.

        Args:
            parser: The argument parser.
            namespace: The namespace to store the parsed arguments.
            values: The argument values.
            option_string: The option string that triggered this action.
        """
        sys_version = sys.version.replace("\n", "")
        env = (
            f"xsget: {__version__}\n"
            f"python: {sys_version}\n"
            f"platform: {platform.platform()}\n"
        )
        parser._print_message(env, sys.stdout)
        parser.exit()


def create_base_parser(
    prog: str,
    description: str,
    epilog: str,
) -> argparse.ArgumentParser:
    """Create a base parser with common arguments."""
    parser = argparse.ArgumentParser(
        prog=prog,
        add_help=False,
        description=description,
        epilog=epilog,
        formatter_class=lambda prog: argparse.RawTextHelpFormatter(
            prog,
            max_help_position=8,
        ),
    )

    parser.add_argument(
        "-q",
        "--quiet",
        default=False,
        action="store_true",
        dest="quiet",
        help="suppress all logging",
    )

    parser.add_argument(
        "-e",
        "--env",
        default=False,
        action=EnvironmentAction,
        dest="env",
        help="print environment information for bug reporting",
    )

    parser.add_argument(
        "-d",
        "--debug",
        default=False,
        action="store_true",
        dest="debug",
        help="show debugging log and stacktrace",
    )

    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="show this help message and exit",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser
