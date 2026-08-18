import requests
import streamlit as st
import plotly.express as px
from config import Config, load_config
from jira_client import get_service_desk_id, get_queue_jql, fetch_issues
from data_processor import build_jql, group_by_assignee, group_by_status, group_by_request_type, compute_kpis

QUEUE_IDS = [37, 31]  # 37 = open/in-progress, 31 = closed/resolved

st.set_page_config(page_title="Ad Ops - EA | Ticket Dashboard", layout="wide")

try:
    config = load_config()
except EnvironmentError as e:
    st.error(str(e))
    st.stop()


@st.cache_data(ttl=3600)
def _get_base_jql(jira_url: str, jira_email: str, jira_api_token: str, queue_id: int) -> str:
    cfg = Config(jira_url=jira_url, jira_email=jira_email, jira_api_token=jira_api_token)
    sd_id = get_service_desk_id(cfg)
    return get_queue_jql(cfg, sd_id, queue_id)


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
    all_issues = {}
    for qid in QUEUE_IDS:
        base_jql = _get_base_jql(config.jira_url, config.jira_email, config.jira_api_token, qid)
        jql = build_jql(base_jql, date_field, period)
        for issue in _get_issues(config.jira_url, config.jira_email, config.jira_api_token, jql):
            all_issues[issue["id"]] = issue
    issues = list(all_issues.values())
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
