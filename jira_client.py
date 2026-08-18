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
    url = f"{config.jira_url}/rest/api/3/search"
    headers = _auth_header(config)
    fields = "assignee,status,issuetype,created,updated"
    issues = []
    start_at = 0
    max_results = 100
    while True:
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": fields,
        }
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        issues.extend(data.get("issues", []))
        if start_at + max_results >= data.get("total", 0):
            break
        start_at += max_results
    return issues
