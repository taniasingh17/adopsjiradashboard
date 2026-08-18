# Ad Ops Jira Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Streamlit web app that shows Jira ticket counts, status breakdowns, and request type distributions for the "Ad Ops - EA" service desk queue, filterable by time period and date mode.

**Architecture:** Four-layer separation: `config.py` loads env vars, `jira_client.py` handles all Jira REST API calls (including fetching the queue's base JQL via the JSM API), `data_processor.py` aggregates raw issues into DataFrames, and `app.py` wires them together with Streamlit UI and Plotly charts.

**Tech Stack:** Python 3.11+, Streamlit, Plotly, pandas, requests, python-dotenv, pytest

**Spec:** `docs/superpowers/specs/2026-08-18-adops-jira-dashboard-design.md`

## Global Constraints

- Python 3.11+
- Jira base URL: `https://mediaiq.atlassian.net`
- Queue: "Ad Ops - EA", project key `TKTS`, queue ID `37`
- Auth: Basic Auth with `JIRA_EMAIL` + `JIRA_API_TOKEN`
- Env vars: `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` — loaded via `os.getenv()` (works both locally with `.env` and on Streamlit Cloud where secrets are injected as env vars)
- API timeout: 10 seconds on all requests
- Pagination: fetch all pages via `startAt` + `maxResults=100`
- Cache: `@st.cache_data(ttl=300)` on issue fetch, `ttl=3600` on queue JQL fetch
- No test file for `app.py` — Streamlit UI tested manually per instructions in Task 5

---

## File Map

| File | Responsibility |
|------|---------------|
| `requirements.txt` | Pinned dependencies |
| `.env.example` | Placeholder credentials (committed) |
| `.env` | Real credentials (gitignored) |
| `config.py` | Load and validate env vars → `Config` dataclass |
| `jira_client.py` | Jira REST + JSM API calls |
| `data_processor.py` | Aggregate raw issues into DataFrames + KPIs |
| `app.py` | Streamlit UI — sidebar, KPI tiles, Plotly charts |
| `tests/test_config.py` | Unit tests for config loading |
| `tests/test_jira_client.py` | Unit tests for API layer (mocked requests) |
| `tests/test_data_processor.py` | Unit tests for all aggregation functions |

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `tests/__init__.py`

**Interfaces:**
- Produces: nothing consumed by code; sets up the environment all subsequent tasks build in

- [ ] **Step 1: Create `requirements.txt`**

```
streamlit>=1.35.0
pandas>=2.0.0
plotly>=5.20.0
requests>=2.31.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

- [ ] **Step 2: Create `.env.example`**

```
JIRA_URL=https://mediaiq.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your_api_token_here
```

- [ ] **Step 3: Create `.gitignore`**

```
.env
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 4: Create `tests/__init__.py`**

Empty file — marks the directory as a Python package for pytest discovery.

```python

```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 6: Initialize git and commit scaffold**

```bash
git init
git add requirements.txt .env.example .gitignore tests/__init__.py
git commit -m "chore: project scaffold"
```

---

## Task 2: `config.py` — Environment Variable Loading

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Produces: `Config` dataclass with fields `jira_url: str`, `jira_email: str`, `jira_api_token: str`; `load_config() -> Config` raises `EnvironmentError` listing all missing var names if any are absent

- [ ] **Step 1: Write failing tests**

Create `tests/test_config.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'config'`

- [ ] **Step 3: Implement `config.py`**

```python
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    jira_url: str
    jira_email: str
    jira_api_token: str


def load_config() -> Config:
    missing = []
    jira_url = os.getenv("JIRA_URL", "")
    jira_email = os.getenv("JIRA_EMAIL", "")
    jira_api_token = os.getenv("JIRA_API_TOKEN", "")

    if not jira_url:
        missing.append("JIRA_URL")
    if not jira_email:
        missing.append("JIRA_EMAIL")
    if not jira_api_token:
        missing.append("JIRA_API_TOKEN")

    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    return Config(
        jira_url=jira_url,
        jira_email=jira_email,
        jira_api_token=jira_api_token,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: config loading with env var validation"
```

---

## Task 3: `jira_client.py` — Jira API Layer

**Files:**
- Create: `jira_client.py`
- Create: `tests/test_jira_client.py`

**Interfaces:**
- Consumes: `Config` from `config.py`
- Produces:
  - `get_service_desk_id(config: Config) -> str` — raises `ValueError` if TKTS desk not found
  - `get_queue_jql(config: Config, service_desk_id: str, queue_id: int) -> str`
  - `fetch_issues(config: Config, jql: str) -> list[dict]` — paginates until all issues fetched; each dict is a raw Jira issue with `fields` key

- [ ] **Step 1: Write failing tests**

Create `tests/test_jira_client.py`:

```python
import pytest
from unittest.mock import patch, MagicMock, call
from config import Config
from jira_client import get_service_desk_id, get_queue_jql, fetch_issues

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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_jira_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'jira_client'`

- [ ] **Step 3: Implement `jira_client.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_jira_client.py -v
```

Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add jira_client.py tests/test_jira_client.py
git commit -m "feat: jira API client with pagination and queue JQL resolution"
```

---

## Task 4: `data_processor.py` — Aggregation

**Files:**
- Create: `data_processor.py`
- Create: `tests/test_data_processor.py`

**Interfaces:**
- Consumes: `list[dict]` from `jira_client.fetch_issues()` — each dict has shape `{"id": str, "fields": {"assignee": {"displayName": str} | None, "status": {"name": str}, "issuetype": {"name": str}}}`
- Produces:
  - `build_jql(base_jql: str, date_field: str, period: str) -> str` — `period` is one of `"today"`, `"week"`, `"month"`; `date_field` is `"created"` or `"updated"`
  - `group_by_assignee(issues: list) -> pd.DataFrame` — columns: `["assignee", "count"]`, sorted descending by count
  - `group_by_status(issues: list) -> pd.DataFrame` — columns: `["assignee", "status", "count"]`
  - `group_by_request_type(issues: list) -> pd.DataFrame` — columns: `["request_type", "count"]`, sorted descending
  - `compute_kpis(issues: list) -> dict` — keys: `"total"` (int), `"done"` (int), `"completion_rate"` (float, one decimal, percent)

- [ ] **Step 1: Write failing tests**

Create `tests/test_data_processor.py`:

```python
import pytest
from data_processor import (
    build_jql,
    group_by_assignee,
    group_by_status,
    group_by_request_type,
    compute_kpis,
)


def make_issue(assignee=None, status="Open", issuetype="Bug"):
    return {
        "id": "1",
        "fields": {
            "assignee": {"displayName": assignee} if assignee else None,
            "status": {"name": status},
            "issuetype": {"name": issuetype},
        },
    }


# --- build_jql ---

def test_build_jql_today_created():
    result = build_jql("project = TKTS", "created", "today")
    assert result == "project = TKTS AND created >= startOfDay()"


def test_build_jql_week_updated():
    result = build_jql("project = TKTS", "updated", "week")
    assert result == "project = TKTS AND updated >= startOfWeek()"


def test_build_jql_month_created():
    result = build_jql("project = TKTS", "created", "month")
    assert result == "project = TKTS AND created >= startOfMonth()"


# --- group_by_assignee ---

def test_group_by_assignee_counts_correctly():
    issues = [
        make_issue("Alice"),
        make_issue("Alice"),
        make_issue("Bob"),
        make_issue(None),
    ]
    df = group_by_assignee(issues)
    assert set(df["assignee"]) == {"Alice", "Bob", "Unassigned"}
    assert df[df["assignee"] == "Alice"]["count"].values[0] == 2
    assert df[df["assignee"] == "Bob"]["count"].values[0] == 1
    assert df[df["assignee"] == "Unassigned"]["count"].values[0] == 1


def test_group_by_assignee_sorted_descending():
    issues = [make_issue("Bob"), make_issue("Alice"), make_issue("Alice")]
    df = group_by_assignee(issues)
    assert df.iloc[0]["assignee"] == "Alice"


def test_group_by_assignee_empty_returns_empty_df():
    df = group_by_assignee([])
    assert list(df.columns) == ["assignee", "count"]
    assert len(df) == 0


# --- group_by_status ---

def test_group_by_status_counts_per_assignee_and_status():
    issues = [
        make_issue("Alice", "Open"),
        make_issue("Alice", "Done"),
        make_issue("Alice", "Open"),
        make_issue("Bob", "Done"),
    ]
    df = group_by_status(issues)
    alice_open = df[(df["assignee"] == "Alice") & (df["status"] == "Open")]["count"].values[0]
    alice_done = df[(df["assignee"] == "Alice") & (df["status"] == "Done")]["count"].values[0]
    bob_done = df[(df["assignee"] == "Bob") & (df["status"] == "Done")]["count"].values[0]
    assert alice_open == 2
    assert alice_done == 1
    assert bob_done == 1


def test_group_by_status_empty_returns_empty_df():
    df = group_by_status([])
    assert list(df.columns) == ["assignee", "status", "count"]
    assert len(df) == 0


# --- group_by_request_type ---

def test_group_by_request_type_counts_correctly():
    issues = [
        make_issue(issuetype="Bug"),
        make_issue(issuetype="Bug"),
        make_issue(issuetype="Task"),
    ]
    df = group_by_request_type(issues)
    assert df[df["request_type"] == "Bug"]["count"].values[0] == 2
    assert df[df["request_type"] == "Task"]["count"].values[0] == 1


def test_group_by_request_type_sorted_descending():
    issues = [make_issue(issuetype="Task"), make_issue(issuetype="Bug"), make_issue(issuetype="Bug")]
    df = group_by_request_type(issues)
    assert df.iloc[0]["request_type"] == "Bug"


def test_group_by_request_type_empty_returns_empty_df():
    df = group_by_request_type([])
    assert list(df.columns) == ["request_type", "count"]
    assert len(df) == 0


# --- compute_kpis ---

def test_compute_kpis_calculates_all_fields():
    issues = [
        make_issue(status="Done"),
        make_issue(status="Done"),
        make_issue(status="Open"),
        make_issue(status="In Progress"),
    ]
    kpis = compute_kpis(issues)
    assert kpis["total"] == 4
    assert kpis["done"] == 2
    assert kpis["completion_rate"] == 50.0


def test_compute_kpis_case_insensitive_done_match():
    issues = [make_issue(status="DONE"), make_issue(status="done"), make_issue(status="Done")]
    kpis = compute_kpis(issues)
    assert kpis["done"] == 3


def test_compute_kpis_empty_issues_returns_zeros():
    kpis = compute_kpis([])
    assert kpis["total"] == 0
    assert kpis["done"] == 0
    assert kpis["completion_rate"] == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_data_processor.py -v
```

Expected: `ModuleNotFoundError: No module named 'data_processor'`

- [ ] **Step 3: Implement `data_processor.py`**

```python
import pandas as pd

_PERIOD_JQL = {
    "today": "startOfDay()",
    "week": "startOfWeek()",
    "month": "startOfMonth()",
}


def build_jql(base_jql: str, date_field: str, period: str) -> str:
    return f"{base_jql} AND {date_field} >= {_PERIOD_JQL[period]}"


def _assignee_name(issue: dict) -> str:
    assignee = issue.get("fields", {}).get("assignee")
    return assignee["displayName"] if assignee else "Unassigned"


def _status_name(issue: dict) -> str:
    return issue.get("fields", {}).get("status", {}).get("name", "Unknown")


def _request_type(issue: dict) -> str:
    return issue.get("fields", {}).get("issuetype", {}).get("name", "Unknown")


def group_by_assignee(issues: list) -> pd.DataFrame:
    if not issues:
        return pd.DataFrame(columns=["assignee", "count"])
    rows = [{"assignee": _assignee_name(i)} for i in issues]
    df = pd.DataFrame(rows)
    return (
        df.groupby("assignee")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )


def group_by_status(issues: list) -> pd.DataFrame:
    if not issues:
        return pd.DataFrame(columns=["assignee", "status", "count"])
    rows = [{"assignee": _assignee_name(i), "status": _status_name(i)} for i in issues]
    df = pd.DataFrame(rows)
    return df.groupby(["assignee", "status"]).size().reset_index(name="count")


def group_by_request_type(issues: list) -> pd.DataFrame:
    if not issues:
        return pd.DataFrame(columns=["request_type", "count"])
    rows = [{"request_type": _request_type(i)} for i in issues]
    df = pd.DataFrame(rows)
    return (
        df.groupby("request_type")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )


def compute_kpis(issues: list) -> dict:
    total = len(issues)
    done = sum(1 for i in issues if _status_name(i).lower() == "done")
    rate = round(done / total * 100, 1) if total > 0 else 0.0
    return {"total": total, "done": done, "completion_rate": rate}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_data_processor.py -v
```

Expected: 14 PASSED

- [ ] **Step 5: Run the full test suite**

```bash
pytest -v
```

Expected: all tests from Tasks 2, 3, and 4 pass (23 total)

- [ ] **Step 6: Commit**

```bash
git add data_processor.py tests/test_data_processor.py
git commit -m "feat: data aggregation — assignee, status, request type, KPIs"
```

---

## Task 5: `app.py` — Streamlit UI

No automated tests for the Streamlit layer — manual testing instructions are provided in the verification steps.

**Files:**
- Create: `app.py`

**Interfaces:**
- Consumes: `load_config` from `config.py`; `get_service_desk_id`, `get_queue_jql`, `fetch_issues` from `jira_client.py`; `build_jql`, `group_by_assignee`, `group_by_status`, `group_by_request_type`, `compute_kpis` from `data_processor.py`

- [ ] **Step 1: Implement `app.py`**

```python
import requests
import streamlit as st
import plotly.express as px
from config import Config, load_config
from jira_client import get_service_desk_id, get_queue_jql, fetch_issues
from data_processor import build_jql, group_by_assignee, group_by_status, group_by_request_type, compute_kpis

QUEUE_ID = 37

st.set_page_config(page_title="Ad Ops - EA | Ticket Dashboard", layout="wide")

try:
    config = load_config()
except EnvironmentError as e:
    st.error(str(e))
    st.stop()


@st.cache_data(ttl=3600)
def _get_base_jql(jira_url: str, jira_email: str, jira_api_token: str) -> str:
    cfg = Config(jira_url=jira_url, jira_email=jira_email, jira_api_token=jira_api_token)
    sd_id = get_service_desk_id(cfg)
    return get_queue_jql(cfg, sd_id, QUEUE_ID)


@st.cache_data(ttl=300)
def _get_issues(jira_url: str, jira_email: str, jira_api_token: str, jql: str) -> list:
    cfg = Config(jira_url=jira_url, jira_email=jira_email, jira_api_token=jira_api_token)
    return fetch_issues(cfg, jql)


# --- Sidebar ---
st.sidebar.title("Filters")

period_label = st.sidebar.radio("Time Period", ["Today", "This Week", "This Month"])
period_map = {"Today": "today", "This Week": "week", "This Month": "month"}
period = period_map[period_label]

date_mode = st.sidebar.radio("Date Mode", ["Created", "Updated"])
date_field = date_mode.lower()

if st.sidebar.button("Refresh"):
    st.cache_data.clear()
    st.rerun()

# --- Main ---
st.title("Ad Ops - EA | Ticket Dashboard")

try:
    base_jql = _get_base_jql(config.jira_url, config.jira_email, config.jira_api_token)
    jql = build_jql(base_jql, date_field, period)
    issues = _get_issues(config.jira_url, config.jira_email, config.jira_api_token, jql)
except requests.exceptions.Timeout:
    st.error("Request timed out — Jira may be unreachable. Try again in a moment.")
    st.stop()
except requests.exceptions.HTTPError as e:
    status = e.response.status_code if e.response is not None else None
    if status in (401, 403):
        st.error("Authentication failed — check your JIRA_EMAIL and JIRA_API_TOKEN.")
    elif status == 404:
        st.error("Queue or project not found — verify JIRA_URL and queue ID 37 exist.")
    else:
        st.error(f"Jira API error ({status}): {e}")
    st.stop()
except Exception as e:
    st.error(f"Unexpected error: {e}")
    st.stop()

if not issues:
    st.info(f"No tickets found for {period_label.lower()} ({date_field}).")
    st.stop()

# --- KPI Row ---
kpis = compute_kpis(issues)
col1, col2, col3 = st.columns(3)
col1.metric("Total Tickets", kpis["total"])
col2.metric("Done", kpis["done"])
col3.metric("Completion Rate", f"{kpis['completion_rate']}%")

st.divider()

# --- Tickets by Assignee ---
st.subheader("Tickets by Assignee")
df_assignee = group_by_assignee(issues)
fig_assignee = px.bar(
    df_assignee,
    x="count",
    y="assignee",
    orientation="h",
    labels={"count": "Ticket Count", "assignee": "Assignee"},
    color_discrete_sequence=["#4C78A8"],
)
fig_assignee.update_layout(yaxis={"categoryorder": "total ascending"}, margin={"l": 10})
st.plotly_chart(fig_assignee, use_container_width=True)

st.divider()

# --- Status Breakdown by Assignee ---
st.subheader("Status Breakdown by Assignee")
df_status = group_by_status(issues)
fig_status = px.bar(
    df_status,
    x="count",
    y="assignee",
    color="status",
    orientation="h",
    barmode="stack",
    labels={"count": "Ticket Count", "assignee": "Assignee", "status": "Status"},
)
fig_status.update_layout(yaxis={"categoryorder": "total ascending"}, margin={"l": 10})
st.plotly_chart(fig_status, use_container_width=True)

st.divider()

# --- Request Type Distribution ---
st.subheader("Request Type Distribution")
df_type = group_by_request_type(issues)
fig_type = px.pie(
    df_type,
    values="count",
    names="request_type",
    hole=0.4,
    labels={"request_type": "Request Type", "count": "Count"},
)
st.plotly_chart(fig_type, use_container_width=True)
```

- [ ] **Step 2: Set up local `.env`**

```bash
cp .env.example .env
```

Then edit `.env` and fill in your real values:
```
JIRA_URL=https://mediaiq.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your_api_token_here
```

- [ ] **Step 3: Run the app locally**

```bash
streamlit run app.py
```

Expected: browser opens to `http://localhost:8501`

- [ ] **Step 4: Manual verification — golden path**

Check each of the following:

1. **KPI tiles appear** — "Total Tickets", "Done", "Completion Rate" show non-zero numbers for "This Month"
2. **Assignee bar chart** — horizontal bars visible, sorted with highest count at bottom (Plotly default for ascending y-axis)
3. **Status breakdown** — stacked bars with multiple colored segments per assignee
4. **Request type donut** — pie chart with a hole, segments labeled by issue type
5. **Time period filter** — switching between Today / This Week / This Month changes ticket counts
6. **Date mode filter** — switching between Created / Updated changes ticket counts
7. **Refresh button** — clicking it reloads data (brief spinner visible)

- [ ] **Step 5: Manual verification — error states**

1. Temporarily set `JIRA_API_TOKEN=badtoken` in `.env`, restart app → red `st.error` banner appears, app stops
2. Restore correct token; set time period to "Today" on a weekend when no tickets were created → blue `st.info` banner appears ("No tickets found...")

- [ ] **Step 6: Commit**

```bash
git add app.py .env.example
git commit -m "feat: streamlit dashboard UI with KPIs, charts, and filters"
```

---

## Deployment to Streamlit Community Cloud

After all tasks are complete:

1. Push the repo to GitHub (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io) → "New app"
3. Select your repo, branch `main`, entry point `app.py`
4. Click "Advanced settings" → "Secrets" and paste:
   ```
   JIRA_URL = "https://mediaiq.atlassian.net"
   JIRA_EMAIL = "your@email.com"
   JIRA_API_TOKEN = "your_api_token_here"
   ```
5. Deploy — Streamlit Cloud injects these as OS environment variables, so `os.getenv()` in `config.py` picks them up automatically
