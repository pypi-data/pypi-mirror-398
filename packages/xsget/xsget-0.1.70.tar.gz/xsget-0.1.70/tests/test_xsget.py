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

import argparse
import asyncio
import logging
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aioresponses import aioresponses

from xsget.xsget import (
    _main_async_logic,
    build_parser,
    extract_urls,
    fetch_url_by_aiohttp,
    fetch_url_by_browser,
    fetch_urls,
    filter_urls,
    http_headers,
    main,
    run,
    url_to_filename,
)

DEFAULT_URL = "http://localhost"


def test_url_to_filename():
    expected = [
        ("http://a.com", "index.html"),
        ("http://a.com/", "index.html"),
        ("http://a.com/123", "123.html"),
        ("http://a.com/123/456", "456.html"),
        ("http://a.com/123/456/789", "789.html"),
        ("http://a.com/123.html", "123.html"),
        ("http://a.com/123.html?abc=def", "123.html"),
    ]
    for url, filename in expected:
        assert url_to_filename(url) == filename

    expected = [
        ("http://a.com/123?id=aaa", "id", "aaa.html"),
        ("http://a.com/456.php?tid=abc", "tid", "abc.html"),
        ("http://a.com/789.php?test=xyz&id=aaa", "id", "aaa.html"),
    ]
    for url, url_param, filename in expected:
        assert url_to_filename(url, url_param) == filename


def test_extract_urls():
    html = """
        <html>
        <body>
        <div class="toc">
            <a href="http://a.com/123"/>a</a>
            <a href="http://a.com/123/789.html"/>b</a>
            <a href="//a.com/987"/>c</a>
            <a href="/123/456"/>d</a>
            <a href="/123/654.html"/>e</a>
        </div>
        </body>
        </html>
    """

    expected_urls = [
        "http://a.com/123",
        "http://a.com/123/789.html",
        "http://a.com/987",
        "http://a.com/123/456",
        "http://a.com/123/654.html",
    ]

    css_paths = [
        "html body div.toc a",
        "html body div a",
        "body div.toc a",
        "div.toc a",
        "div a",
        "a",
    ]
    for css_path in css_paths:
        config = argparse.Namespace(
            url="http://a.com/123",
            link_css_path=css_path,
        )
        assert extract_urls(html, config) == expected_urls


def test_user_agent():
    user_agent = http_headers()["User-Agent"]
    assert "Mozilla/5.0" in user_agent


@patch("sys.stdin")
def test_build_parser_url_arg(mock_stdin):
    mock_stdin.isatty.return_value = True
    parser = build_parser([])
    with pytest.raises(SystemExit):
        parser.parse_args([])

    mock_stdin.isatty.return_value = False
    mock_stdin.read.return_value = "http://piped.url\n"
    parser = build_parser([])
    args = parser.parse_args([])
    assert args.url == "http://piped.url"

    mock_stdin.isatty.return_value = False
    mock_stdin.read.return_value = "http://piped.url\n"
    parser = build_parser(["http://cli.url"])
    args = parser.parse_args(["http://cli.url"])
    assert args.url == "http://cli.url"

    mock_stdin.isatty.return_value = True
    parser = build_parser(["-c"])
    args = parser.parse_args(["-c"])
    assert args.url == ""
    assert args.config == "xsget.toml"

    parser = build_parser(["-e"])
    url_action = next((a for a in parser._actions if a.dest == "url"), None)
    assert url_action is None


async def test_fetch_url_by_aiohttp(tmp_path, caplog):
    session = aiohttp.ClientSession()
    test_url = "http://test.com/page1"
    test_content = "<html>test content</html>"
    output_dir = tmp_path / "output"
    config = argparse.Namespace(
        url_param_as_filename="",
        output_dir=str(output_dir),
    )

    with aioresponses() as mocked:
        mocked.get(
            test_url,
            status=200,
            body=test_content,
            headers={"Content-Type": "text/html; charset=utf-8"},
        )

        with caplog.at_level(logging.INFO):
            result = await fetch_url_by_aiohttp(session, test_url, config)
            assert result is None

        expected_file = output_dir / "page1.html"
        assert expected_file.exists()
        assert expected_file.read_text(encoding="utf-8") == test_content

        assert "Fetching http://test.com/page1" in caplog.text
        assert f"-> Saving {expected_file}" in caplog.text

    with aioresponses() as mocked:
        mocked.get(test_url, status=404)

        with caplog.at_level(logging.ERROR):
            result = await fetch_url_by_aiohttp(session, test_url, config)
            assert result is None
            assert (
                "error: 404, message='Not Found', url='http://test.com/page1'"
                in caplog.text
            )

    invalid_url = "invalid url"
    with pytest.raises(RuntimeError, match="invalid url: invalid%20url"):
        await fetch_url_by_aiohttp(session, invalid_url, config)
    await session.close()


async def test_fetch_url_by_browser_success(tmp_path, caplog):
    test_url = "http://test.com/page1"
    test_content = "<html>browser content</html>"
    output_dir = tmp_path / "output"
    config = argparse.Namespace(
        url_param_as_filename="",
        output_dir=str(output_dir),
        browser_delay=100,
    )

    mock_response = AsyncMock()
    mock_response.header_value.return_value = "text/html; charset=iso-8859-1"
    mock_page = AsyncMock()
    mock_page.goto.return_value = mock_response
    mock_page.content.return_value = test_content
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page

    with caplog.at_level(logging.INFO):
        await fetch_url_by_browser(mock_context, test_url, config)

    mock_context.new_page.assert_called_once()
    mock_page.wait_for_timeout.assert_called_once_with(config.browser_delay)
    mock_page.goto.assert_called_once_with(test_url)
    mock_page.content.assert_called_once()
    mock_page.close.assert_called_once()

    expected_file = output_dir / "page1.html"
    assert expected_file.exists()
    assert expected_file.read_text(encoding="iso-8859-1") == test_content
    assert f"Fetch: {test_url} -> save: {expected_file}" in caplog.text


async def test_fetch_url_by_browser_encoding_fallback(tmp_path, caplog):
    test_url = "http://test.com/page2"
    test_content = "<html>browser content</html>"
    output_dir = tmp_path / "output_fallback"
    config = argparse.Namespace(
        url_param_as_filename="",
        output_dir=str(output_dir),
        browser_delay=0,
    )

    mock_response = AsyncMock()
    mock_response.header_value.return_value = "a=b;c"
    mock_page = AsyncMock()
    mock_page.goto.return_value = mock_response
    mock_page.content.return_value = test_content
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page
    with caplog.at_level(logging.WARNING):
        await fetch_url_by_browser(mock_context, test_url, config)

    expected_file = output_dir / "page2.html"
    assert expected_file.exists()
    assert expected_file.read_text(encoding="utf-8") == test_content
    assert "Could not parse encoding from content-type" in caplog.text


async def test_fetch_url_by_browser_errors(tmp_path, caplog):
    from playwright.async_api import TimeoutError

    test_url = "http://test.com/error"
    output_dir = tmp_path / "output_error"
    config = argparse.Namespace(
        url_param_as_filename="",
        output_dir=str(output_dir),
        browser_delay=0,
    )

    # Mock Playwright objects
    mock_page = AsyncMock()
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page
    # Test TimeoutError
    mock_page.goto.side_effect = TimeoutError("Page timed out")
    with caplog.at_level(logging.ERROR):
        await fetch_url_by_browser(mock_context, test_url, config)
        assert (
            "Error fetching URL "
            "http://test.com/error with browser: Page timed out" in caplog.text
        )
    mock_page.close.assert_called_once()
    mock_page.close.reset_mock()

    # Test None response
    mock_page.goto.side_effect = None
    mock_page.goto.return_value = None
    with caplog.at_level(logging.ERROR):
        await fetch_url_by_browser(mock_context, test_url, config)
        assert (
            "Failed to get response for URL: http://test.com/error"
            in caplog.text
        )
    mock_page.close.assert_called_once()
    mock_page.close.reset_mock()

    # Test LookupError fallback
    test_url_lookup = "http://test.com/lookup"
    config_lookup = argparse.Namespace(
        url_param_as_filename="",
        output_dir=str(tmp_path / "output_lookup"),
        browser_delay=0,
    )
    mock_response_lookup = AsyncMock()
    mock_response_lookup.header_value.return_value = (
        "text/html; charset=invalid-encoding-name"
    )
    mock_page_lookup = AsyncMock()
    mock_page_lookup.goto.return_value = mock_response_lookup
    mock_page_lookup.content.return_value = "content"
    mock_context_lookup = AsyncMock()
    mock_context_lookup.new_page.return_value = mock_page_lookup
    with caplog.at_level(logging.INFO):
        await fetch_url_by_browser(
            mock_context_lookup,
            test_url_lookup,
            config_lookup,
        )
        assert "Unknown encoding 'invalid-encoding-name'" in caplog.text
        assert "Saved" in caplog.text

    expected_file_lookup = tmp_path / "output_lookup" / "lookup.html"
    assert expected_file_lookup.exists()
    assert expected_file_lookup.read_text(encoding="utf-8") == "content"


@patch("xsget.xsget._main_async_logic", new_callable=AsyncMock)
def test_run(mock_main_async_logic):
    config = argparse.Namespace(debug=True)
    run(config)
    mock_main_async_logic.assert_called_once_with(config)


@patch("xsget.xsget.run")
@patch("xsget.xsget.load_or_create_config", return_value={})
@patch("xsget.xsget.setup_logging")
@patch("xsget.xsget.build_parser")
def test_main_success(
    mock_build_parser,
    mock_setup_logging,
    mock_load_or_create_config,
    mock_run,
):
    mock_parser = MagicMock()
    mock_parser.parse_args.return_value = argparse.Namespace(
        url="http://test.com",
        debug=False,
    )
    mock_build_parser.return_value = mock_parser

    main(["http://test.com"])

    mock_setup_logging.assert_called_once()
    mock_load_or_create_config.assert_called_once()
    mock_run.assert_called_once()


@patch("xsget.xsget.run")
@patch(
    "xsget.xsget.load_or_create_config",
    side_effect=Exception("Config Error"),
)
@patch("xsget.xsget.setup_logging")
@patch("xsget.xsget.build_parser")
def test_main_error_handling(
    mock_build_parser,
    mock_run,
    caplog,
):
    mock_parser = MagicMock()
    mock_parser.parse_args.return_value = argparse.Namespace(
        url="http://test.com",
        debug=False,
    )
    mock_build_parser.return_value = mock_parser

    with pytest.raises(SystemExit) as excinfo:
        with caplog.at_level(logging.ERROR):
            main(["http://test.com"])

    assert excinfo.value.code == 1
    assert "error: Config Error" in caplog.text
    mock_run.assert_not_called()


@patch("xsget.xsget.run")
@patch(
    "xsget.xsget.load_or_create_config",
    side_effect=Exception("Debug Error"),
)
@patch("xsget.xsget.setup_logging")
@patch("xsget.xsget.build_parser")
def test_main_error_handling_debug(
    mock_build_parser,
    mock_run,
    caplog,
):
    mock_parser = MagicMock()
    mock_parser.parse_args.return_value = argparse.Namespace(
        url="http://test.com",
        debug=True,
    )
    mock_build_parser.return_value = mock_parser

    with pytest.raises(SystemExit) as excinfo:
        with caplog.at_level(logging.ERROR):
            main(["http://test.com", "-d"])

    assert excinfo.value.code == 1
    assert "error: Debug Error" in caplog.text
    mock_run.assert_not_called()


@patch("xsget.xsget.fetch_url_by_aiohttp", new_callable=AsyncMock)
async def test_fetch_urls_aiohttp(mock_fetch_aiohttp):
    urls = [["http://a.com/1", "http://a.com/2"]]
    config = argparse.Namespace(browser=False)

    await fetch_urls(urls, config)

    assert mock_fetch_aiohttp.call_count == 2
    mock_fetch_aiohttp.assert_any_call(ANY, "http://a.com/1", config)
    mock_fetch_aiohttp.assert_any_call(ANY, "http://a.com/2", config)


@patch("xsget.xsget.fetch_url_by_browser", new_callable=AsyncMock)
@patch("xsget.xsget.async_playwright")
async def test_fetch_urls_browser(mock_playwright, mock_fetch_browser):
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser  # noqa
    mock_browser.new_context.return_value = mock_context

    urls = [["http://b.com/1", "http://b.com/2"], ["http://b.com/3"]]
    config = argparse.Namespace(browser=True, browser_session=2)

    await fetch_urls(urls, config)

    mock_playwright.assert_called_once()
    mock_browser.new_context.assert_called_once()
    mock_browser.close.assert_called_once()
    mock_context.close.assert_called_once()

    assert mock_fetch_browser.call_count == 3
    mock_fetch_browser.assert_any_call(mock_context, "http://b.com/1", config)
    mock_fetch_browser.assert_any_call(mock_context, "http://b.com/2", config)
    mock_fetch_browser.assert_any_call(mock_context, "http://b.com/3", config)


@patch("xsget.xsget.extract_urls")
def test_filter_urls(mock_extract_urls, tmp_path, caplog):
    index_file = tmp_path / "index.html"
    index_file.write_text("<html>index</html>", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    all_urls = [
        "http://a.com/new",
        "http://a.com/existing",
        "http://a.com/undecodable",
    ]
    mock_extract_urls.side_effect = [all_urls, all_urls, []]

    existing_filename = url_to_filename("http://a.com/existing")
    (output_dir / existing_filename).touch()

    config = argparse.Namespace(
        url_param_as_filename="",
        output_dir=str(output_dir),
        browser=False,
        browser_session=0,
    )

    with caplog.at_level(logging.INFO):
        burls = filter_urls(index_file, config)

    expected_urls = ["http://a.com/new", "http://a.com/undecodable"]
    assert burls == [expected_urls]
    assert "Total URL extracted: 3" in caplog.text
    assert "Total URL to download: 2" in caplog.text
    assert "Total URL batches to download: 1" in caplog.text

    config.browser = True
    config.browser_session = 1
    caplog.clear()
    with caplog.at_level(logging.INFO):
        burls = filter_urls(index_file, config)
    assert burls == [["http://a.com/new"], ["http://a.com/undecodable"]]
    assert "Total URL batches to download: 2" in caplog.text

    index_file_empty = tmp_path / "empty.html"
    index_file_empty.write_bytes(b"")
    config.browser = False
    config.browser_session = 0
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        burls = filter_urls(index_file_empty, config)
        assert burls == []


@patch("xsget.xsget.fetch_urls", new_callable=AsyncMock)
@patch("xsget.xsget.filter_urls")
def test_main_async_logic_range(mock_filter_urls, mock_fetch_urls):
    config = argparse.Namespace(
        url="http://test.com/page[1-3].html",
        url_param_as_filename="",
        output_dir="output",
        test=False,
    )
    asyncio.run(_main_async_logic(config))

    expected_urls = [
        "http://test.com/page1.html",
        "http://test.com/page2.html",
        "http://test.com/page3.html",
    ]
    mock_fetch_urls.assert_called_once_with([expected_urls], config)
    mock_filter_urls.assert_not_called()


@patch("xsget.xsget.fetch_urls", new_callable=AsyncMock)
@patch("xsget.xsget.filter_urls")
def test_main_async_logic_range_invalid(mock_filter_urls, mock_fetch_urls):
    config = argparse.Namespace(
        url="http://test.com/page[3-1].html",
        url_param_as_filename="",
        output_dir="output",
        test=False,
    )
    with pytest.raises(
        RuntimeError,
        match="invalid url range, start: 3, end: 1",
    ):
        asyncio.run(_main_async_logic(config))

    mock_fetch_urls.assert_not_called()
    mock_filter_urls.assert_not_called()


@patch("xsget.xsget.fetch_urls", new_callable=AsyncMock)
@patch("xsget.xsget.filter_urls")
def test_main_async_logic_single_url_crawl(
    mock_filter_urls,
    mock_fetch_urls,
    tmp_path,
):
    test_url = "http://test.com/index"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    index_filename = url_to_filename(test_url)
    index_path = output_dir / index_filename
    index_path.touch()

    config = argparse.Namespace(
        url=test_url,
        url_param_as_filename="",
        output_dir=str(output_dir),
        refresh=False,
        test=False,
    )

    mock_filter_urls.return_value = [["http://test.com/chap1"]]

    asyncio.run(_main_async_logic(config))

    mock_fetch_urls.assert_any_call([[test_url]], config)
    mock_filter_urls.assert_called_once_with(index_path, config)
    mock_fetch_urls.assert_any_call([["http://test.com/chap1"]], config)
    assert mock_fetch_urls.call_count == 2


@patch("xsget.xsget.fetch_urls", new_callable=AsyncMock)
@patch("xsget.xsget.filter_urls")
def test_main_async_logic_single_url_refresh(
    mock_filter_urls,
    mock_fetch_urls,
    tmp_path,
    caplog,
):
    test_url = "http://test.com/index"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    index_filename = url_to_filename(test_url)
    index_path = output_dir / index_filename
    index_path.touch()

    config = argparse.Namespace(
        url=test_url,
        url_param_as_filename="",
        output_dir=str(output_dir),
        refresh=True,
        test=False,
    )

    mock_filter_urls.return_value = [["http://test.com/chap1"]]

    with caplog.at_level(logging.INFO):
        asyncio.run(_main_async_logic(config))

    assert not index_path.exists()
    assert "Refresh the index url: http://test.com/index" in caplog.text
    mock_fetch_urls.assert_any_call([[test_url]], config)
    mock_filter_urls.assert_called_once_with(index_path, config)
    mock_fetch_urls.assert_any_call([["http://test.com/chap1"]], config)
    assert mock_fetch_urls.call_count == 2


@patch("xsget.xsget.fetch_urls", new_callable=AsyncMock)
@patch("xsget.xsget.filter_urls")
def test_main_async_logic_test_mode(
    mock_filter_urls,
    mock_fetch_urls,
    tmp_path,
    caplog,
):
    test_url = "http://test.com/index"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    index_filename = url_to_filename(test_url)
    index_path = output_dir / index_filename
    index_path.touch()

    config = argparse.Namespace(
        url=test_url,
        url_param_as_filename="",
        output_dir=str(output_dir),
        refresh=False,
        test=True,
    )

    mock_filter_urls.return_value = [
        ["http://test.com/chap1", "http://test.com/chap2"],
    ]

    with caplog.at_level(logging.INFO):
        asyncio.run(_main_async_logic(config))

    mock_fetch_urls.assert_called_once_with([[test_url]], config)
    mock_filter_urls.assert_called_once_with(index_path, config)
    assert "Found url: http://test.com/chap1" in caplog.text
    assert "Found url: http://test.com/chap2" in caplog.text
    assert mock_fetch_urls.call_count == 1
