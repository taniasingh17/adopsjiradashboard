import pytest
from unittest.mock import patch, MagicMock
from config import Config
from jira_client import get_service_desk_id, get_queue_jql, fetch_issues, _auth_header

CONFIG = Config(
    jira_url="https://test.atlassian.net",
    jira_email="user@test.com",
    jira_api_token="token123",
)


def _mock_response(json_data):
    mock = MagicMock()
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


def test_get_service_desk_id_returns_id_for_tkts():
    response = _mock_response({
        "values": [
            {"id": "1", "projectKey": "OTHER"},
            {"id": "42", "projectKey": "TKTS"},
        ]
    })
    with patch("jira_client.requests.get", return_value=response):
        result = get_service_desk_id(CONFIG)
    assert result == "42"


def test_get_service_desk_id_raises_when_tkts_not_found():
    response = _mock_response({"values": [{"id": "1", "projectKey": "OTHER"}]})
    with patch("jira_client.requests.get", return_value=response):
        with pytest.raises(ValueError, match="TKTS"):
            get_service_desk_id(CONFIG)


def test_get_queue_jql_returns_jql_string():
    response = _mock_response({"jql": "project = TKTS AND type in (Story)"})
    with patch("jira_client.requests.get", return_value=response):
        result = get_queue_jql(CONFIG, "42", 37)
    assert result == "project = TKTS AND type in (Story)"


def test_fetch_issues_single_page():
    response = _mock_response({
        "issues": [{"id": "1", "fields": {"assignee": None}}],
        "total": 1,
    })
    with patch("jira_client.requests.get", return_value=response):
        result = fetch_issues(CONFIG, "project = TKTS")
    assert len(result) == 1
    assert result[0]["id"] == "1"


def test_fetch_issues_paginates_until_all_fetched():
    page1 = _mock_response({
        "issues": [{"id": str(i), "fields": {}} for i in range(100)],
        "total": 150,
    })
    page2 = _mock_response({
        "issues": [{"id": str(i), "fields": {}} for i in range(100, 150)],
        "total": 150,
    })
    with patch("jira_client.requests.get", side_effect=[page1, page2]):
        result = fetch_issues(CONFIG, "project = TKTS")
    assert len(result) == 150


def test_fetch_issues_empty_result():
    response = _mock_response({"issues": [], "total": 0})
    with patch("jira_client.requests.get", return_value=response):
        result = fetch_issues(CONFIG, "project = TKTS AND created >= startOfDay()")
    assert result == []


def test_auth_header_encodes_credentials_correctly():
    import base64
    headers = _auth_header(CONFIG)
    assert headers["Accept"] == "application/json"
    assert headers["Authorization"].startswith("Basic ")
    encoded = headers["Authorization"][len("Basic "):]
    decoded = base64.b64decode(encoded).decode()
    assert decoded == "user@test.com:token123"
