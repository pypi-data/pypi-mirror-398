# Copyright (C) 2021,2022,2023,2024,2025 Kian-Meng Ang
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

"""Console tools to download online novel and convert to text file."""

import logging
from importlib import metadata

from .config import (
    ConfigFileCorruptedError as ConfigFileCorruptedError,
)
from .config import (
    ConfigFileExistsError as ConfigFileExistsError,
)
from .config import (
    load_or_create_config as load_or_create_config,
)
from .config import (
    setup_logging as setup_logging,
)

__version__ = metadata.version("xsget")

_logger = logging.getLogger(__name__)
