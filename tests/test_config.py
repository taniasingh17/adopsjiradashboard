import pytest
from unittest.mock import patch
from config import load_config, Config


def test_load_config_returns_config_dataclass():
    env = {
        "JIRA_URL": "https://test.atlassian.net",
        "JIRA_EMAIL": "user@test.com",
        "JIRA_API_TOKEN": "token123",
    }
    with patch.dict("os.environ", env, clear=True):
        config = load_config()
    assert isinstance(config, Config)
    assert config.jira_url == "https://test.atlassian.net"
    assert config.jira_email == "user@test.com"
    assert config.jira_api_token == "token123"


def test_load_config_raises_when_all_vars_missing():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(EnvironmentError) as exc_info:
            load_config()
    msg = str(exc_info.value)
    assert "JIRA_URL" in msg
    assert "JIRA_EMAIL" in msg
    assert "JIRA_API_TOKEN" in msg


def test_load_config_raises_when_partial_vars_missing():
    with patch.dict("os.environ", {"JIRA_URL": "https://test.atlassian.net"}, clear=True):
        with pytest.raises(EnvironmentError) as exc_info:
            load_config()
    msg = str(exc_info.value)
    assert "JIRA_EMAIL" in msg
    assert "JIRA_API_TOKEN" in msg
    assert "JIRA_URL" not in msg
