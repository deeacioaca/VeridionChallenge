import aiohttp
import pytest
from unittest.mock import AsyncMock, patch

from scraper.crawler import extract_phone_numbers, extract_social_links, extract_address, _decode_response, _fetch, \
    fetch_html, try_fetch_with_fallback


@pytest.mark.parametrize("html,expected_phones", [
    ("Call us at +1 234 567 8901 or (123) 456-7890", ["+1 234 567 8901", "(123) 456-7890"]),
    ("Phone: 123-456-7890, 1-800-555-1234", ["123-456-7890", "1-800-555-1234"]),
    ("No phone here", []),
])
def test_extract_phone_numbers(html, expected_phones):
    phones = extract_phone_numbers(html)
    for p in expected_phones:
        assert p in phones

@pytest.mark.parametrize("html,expected_links", [
    ('<a href="https://facebook.com/user">fb</a><a href="https://twitter.com/user">tw</a>',
     ["https://facebook.com/user", "https://twitter.com/user"]),
    ('<a href="https://example.com">no social</a>', []),
])
def test_extract_social_links(html, expected_links):
    links = extract_social_links(html)
    for l in expected_links:
        assert l in links
    assert all(l in expected_links for l in links)

@pytest.mark.parametrize("html,expected_address", [
    ("<address>123 Main St, NY 12345</address>", "123 Main St, NY 12345"),
    ('<div class="address">456 Elm St, CA 90210</div>', "456 Elm St, CA 90210"),
    ("Random text 789 Oak St, TX 75001 somewhere", "789 Oak St, TX 75001"),
    ("No address here", None),
])
def test_extract_address(html, expected_address):
    addr = extract_address(html)
    assert addr == expected_address

@pytest.mark.asyncio
async def test_decode_response_success():
    # Mock response.text returns "test"
    class DummyResp:
        async def text(self):
            return "test"
    resp = DummyResp()
    result = await _decode_response(resp)
    assert result == "test"

@pytest.mark.asyncio
async def test_decode_response_unicode_error():
    class DummyResp:
        async def text(self):
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "reason")
        async def read(self):
            return b"fallback bytes"
    resp = DummyResp()
    result = await _decode_response(resp)
    assert isinstance(result, str)

@pytest.mark.asyncio
@patch("scraper.crawler._decode_response")
@patch("scraper.crawler.aiohttp.ClientSession.get")
async def test_fetch_success(mock_get, mock_decode):
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_decode.return_value = "<html></html>"
    mock_get.return_value.__aenter__.return_value = mock_response

    async with aiohttp.ClientSession() as session:
        html, status = await _fetch(session, "http://test.com", ssl_flag=False)

    assert html == "<html></html>"
    assert status == 200

@pytest.mark.asyncio
@patch("scraper.crawler._fetch")
async def test_fetch_html_retries(mock_fetch):
    # Simulate first fetch fails, second succeeds
    mock_fetch.side_effect = [(None, 500), ("<html></html>", 200)]

    session = AsyncMock()
    html, status = await fetch_html(session, "http://test.com", retries=2, delay=0)

    assert html == "<html></html>"
    assert status == 200

@pytest.mark.asyncio
@patch("scraper.crawler.fetch_html")
async def test_try_fetch_with_fallback(mock_fetch_html):
    # Only 4 calls expected: https + www, https + no www, http + www, http + no www
    mock_fetch_html.side_effect = [
        (None, 404),  # https://www.domain
        (None, 404),  # https://domain
        (None, 404),  # http://www.domain
        ("<html></html>", 200),  # http://domain success
    ]
    session = AsyncMock()
    url, html, status = await try_fetch_with_fallback(session, "domain")

    assert html is not None
    assert status == 200
    assert url.startswith("http://")
