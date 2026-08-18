import base64
import requests
from config import Config

QUEUE_ID = 37


def _auth_header(config: Config) -> dict:
    credentials = f"{config.jira_email}:{config.jira_api_token}"
    token = base64.b64encode(credentials.encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
    }


def get_service_desk_id(config: Config) -> str:
    url = f"{config.jira_url}/rest/servicedeskapi/servicedesk"
    response = requests.get(url, headers=_auth_header(config), timeout=10)
    response.raise_for_status()
    for desk in response.json().get("values", []):
        if desk.get("projectKey") == "TKTS":
            return desk["id"]
    raise ValueError("Service desk for project TKTS not found")


def get_queue_jql(config: Config, service_desk_id: str, queue_id: int = QUEUE_ID) -> str:
    url = f"{config.jira_url}/rest/servicedeskapi/servicedesk/{service_desk_id}/queue/{queue_id}"
    response = requests.get(url, headers=_auth_header(config), timeout=10)
    response.raise_for_status()
    return response.json()["jql"]


def fetch_issues(config: Config, jql: str) -> list:
    url = f"{config.jira_url}/rest/api/3/search/jql"
    headers = _auth_header(config)
    fields = "assignee,status,issuetype,created,updated"
    issues = []
    next_page_token = None
    while True:
        params = {"jql": jql, "maxResults": 100, "fields": fields}
        if next_page_token:
            params["nextPageToken"] = next_page_token
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        batch = data.get("issues", [])
        issues.extend(batch)
        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break
    return issues
