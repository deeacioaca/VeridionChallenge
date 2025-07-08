import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.api import app

client = TestClient(app)

# Sample company data to be returned by mocked ES search
mock_company = {
    "_source": {
        "company_commercial_name": "Test Company",
        "company_all_available_names": ["Test Co", "Test Company"],
        "domain": "testcompany.com",
        "phone_numbers": ["1234567890"],
        "social_links": ["https://facebook.com/testcompany"]
    }
}

@pytest.fixture
def es_search_mock():
    with patch("api.api.es.search") as mock_search:
        yield mock_search

def test_match_company_found(es_search_mock):
    # Mock ES to return a hit
    es_search_mock.return_value = {
        "hits": {
            "hits": [mock_company]
        }
    }

    response = client.post("/match_company", json={
        "name": "Test Company",
        "website": "https://testcompany.com",
        "phone": "(123) 456-7890",
        "facebook": "https://facebook.com/testcompany"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["match_found"] is True
    assert data["company_profile"] == mock_company["_source"]

def test_match_company_not_found(es_search_mock):
    # Mock ES to return no hits
    es_search_mock.return_value = {
        "hits": {
            "hits": []
        }
    }

    response = client.post("/match_company", json={"name": "No Company"})
    assert response.status_code == 200
    data = response.json()
    assert data["match_found"] is False
    assert data["company_profile"] is None

def test_match_company_partial_fields(es_search_mock):
    # Test request with only phone number
    es_search_mock.return_value = {
        "hits": {
            "hits": [mock_company]
        }
    }

    response = client.post("/match_company", json={"phone": "1234567890"})
    assert response.status_code == 200
    data = response.json()
    assert data["match_found"] is True
