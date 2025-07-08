import pytest
from unittest.mock import AsyncMock, patch
from scraper.run_scraper import process_domain, failed_domains, run_scraper

@pytest.mark.asyncio
@patch("scraper.run_scraper.try_fetch_with_fallback")
async def test_process_domain_failure(mock_try_fetch):
    mock_try_fetch.return_value = (None, None, 404)

    session = AsyncMock()

    # Clear failed_domains before test
    failed_domains.clear()

    result = await process_domain(session, "nonexistent.com", 2)

    assert result is None
    assert ("nonexistent.com", 404) in failed_domains

@pytest.mark.asyncio
@patch("scraper.run_scraper.pd.read_csv")
@patch("scraper.run_scraper.pd.DataFrame.to_csv")
@patch("scraper.run_scraper.process_domain")
@patch("aiohttp.ClientSession")
async def test_run_scraper(mock_session_class, mock_process_domain, mock_to_csv, mock_read_csv):
    # Setup mock CSV reading to return a dataframe with domains
    import pandas as pd
    mock_read_csv.return_value = pd.DataFrame({"domain": ["example.com", "test.com"]})

    # Mock aiohttp.ClientSession context manager
    mock_session = AsyncMock()
    mock_session_class.return_value.__aenter__.return_value = mock_session

    # Mock process_domain to return dummy data for both domains
    mock_process_domain.side_effect = [
        {"domain": "example.com", "phone_numbers": "123", "social_links": "fb", "address": "addr1"},
        {"domain": "test.com", "phone_numbers": "456", "social_links": "tw", "address": "addr2"},
    ]

    # Run scraper
    await run_scraper()

    # Assert read_csv called once with input path
    mock_read_csv.assert_called_once()

    # Assert process_domain called twice
    assert mock_process_domain.call_count == 2

    # Assert to_csv called at least once for output CSV
    assert mock_to_csv.call_count >= 1

