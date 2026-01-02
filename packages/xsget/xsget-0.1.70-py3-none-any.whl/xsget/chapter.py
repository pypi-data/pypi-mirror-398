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

"""Data model for an extracted Chapter."""

from dataclasses import dataclass, field


@dataclass(repr=False)
class Chapter:
    """A Chapter model class."""

    title: str = field(default="")
    content: str = field(default="")
    content_path: str = field(default="")
    filename: str = field(default="")

    def __repr__(self) -> str:
        """Return the canonical string representation of the object."""
        return (
            f"Chapter(content='{self.content}', title='{self.title}', "
            f"filename='{self.filename}', content_path='{self.content_path}')"
        )

    def __str__(self) -> str:
        """Return the string representation of the object."""
        if self.title and self.content:
            return f"{self.title}\n\n{self.content}"
        if self.title:
            return self.title
        if self.content:
            return self.content
        return ""
