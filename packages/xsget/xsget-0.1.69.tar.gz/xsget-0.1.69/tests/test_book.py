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

from xsget.book import Book
from xsget.chapter import Chapter


def test_book_dataclass_default_values():
    """Test Book dataclass with default values."""
    book = Book()
    assert book.title == ""
    assert book.authors == []
    assert book.chapters == []


def test_book_dataclass_custom_values():
    """Test Book dataclass with custom values."""
    chapter1 = Chapter(title="Chapter 1", content="Content of chapter 1")
    chapter2 = Chapter(title="Chapter 2", content="Content of chapter 2")
    book = Book(
        title="My Awesome Book",
        authors=["Author One", "Author Two"],
        chapters=[chapter1, chapter2],
    )
    assert book.title == "My Awesome Book"
    assert book.authors == ["Author One", "Author Two"]
    assert len(book.chapters) == 2
    assert book.chapters[0].title == "Chapter 1"
    assert book.chapters[1].title == "Chapter 2"
