import requests
import streamlit as st
import plotly.express as px
from config import Config, load_config
from jira_client import fetch_issues
from data_processor import build_jql, build_jql_range, group_by_assignee, group_by_status, group_by_request_type, compute_kpis

BASE_JQL = "project = TKTS"
BRAND_COLORS = ["#F2226E", "#F2911B", "#F26A1B", "#D92323", "#220126"]
CHART_HEIGHT = 420

st.set_page_config(page_title="Ad Ops - EA | Ticket Dashboard", layout="wide")
st.logo("logo.png")

try:
    config = load_config()
except EnvironmentError as e:
    st.error(str(e))
    st.stop()


@st.cache_data(ttl=300)
def _get_issues(jira_url: str, jira_email: str, jira_api_token: str, jql: str) -> list:
    cfg = Config(jira_url=jira_url, jira_email=jira_email, jira_api_token=jira_api_token)
    return fetch_issues(cfg, jql)


# --- Sidebar ---
st.sidebar.title("Filters")

period_label = st.sidebar.radio("Time Period", ["Today", "This Week", "This Month", "Custom Range"])
period_map = {"Today": "today", "This Week": "week", "This Month": "month"}

custom_start = custom_end = None
if period_label == "Custom Range":
    import datetime
    today = datetime.date.today()
    date_range = st.sidebar.date_input(
        "Select date range",
        value=(today - datetime.timedelta(days=7), today),
        max_value=today,
    )
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        custom_start, custom_end = date_range
    else:
        st.sidebar.warning("Please select a start and end date.")

date_mode = st.sidebar.radio("Date Mode", ["Created", "Updated"])
date_field = date_mode.lower()

if st.sidebar.button("Refresh"):
    st.cache_data.clear()
    st.rerun()


# --- Main ---
st.title("Ad Ops - EA | Ticket Dashboard")

if period_label == "Custom Range" and not (custom_start and custom_end):
    st.info("Select a start and end date to load tickets.")
    st.stop()

try:
    if period_label == "Custom Range":
        jql = build_jql_range(BASE_JQL, date_field, custom_start, custom_end)
    else:
        jql = build_jql(BASE_JQL, date_field, period_map[period_label])
    issues = _get_issues(config.jira_url, config.jira_email, config.jira_api_token, jql)
except requests.exceptions.Timeout:
    st.error("Request timed out — Jira may be unreachable. Try again in a moment.")
    st.stop()
except requests.exceptions.HTTPError as e:
    status = e.response.status_code if e.response is not None else None
    if status in (401, 403):
        st.error("Authentication failed — check your JIRA_EMAIL and JIRA_API_TOKEN.")
    elif status == 404:
        st.error("Project not found — verify JIRA_URL and that project TKTS exists.")
    else:
        st.error(f"Jira API error ({status}): {e}")
    st.stop()
except Exception as e:
    st.error(f"Unexpected error: {e}")
    st.stop()

if not issues:
    st.info(f"No tickets found for {period_label.lower()} ({date_field}).")
    st.stop()

with st.sidebar.expander("Debug"):
    from data_processor import _status_name as _sn
    st.caption("JQL sent to Jira:")
    st.code(jql, language="text")
    st.caption(f"Tickets returned by API: {len(issues)}")
    statuses = sorted({_sn(i) for i in issues})
    st.caption("Status names in data:")
    st.write(statuses)

# --- KPI Row ---
kpis = compute_kpis(issues)
col1, col2, col3 = st.columns(3)
col1.metric("Total Tickets", kpis["total"])
col2.metric("Done", kpis["done"])
col3.metric("Completion Rate", f"{kpis['completion_rate']}%")

# --- Charts side by side ---
col_left, col_right = st.columns(2)

with col_left:
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
        color_discrete_sequence=BRAND_COLORS,
        height=CHART_HEIGHT,
    )
    fig_status.update_layout(
        yaxis={"categoryorder": "total ascending"},
        margin={"l": 10, "t": 10, "b": 10, "r": 10},
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.3},
    )
    st.plotly_chart(fig_status, use_container_width=True)

with col_right:
    st.subheader("Request Type Distribution")
    df_type = group_by_request_type(issues)
    fig_type = px.pie(
        df_type,
        values="count",
        names="request_type",
        hole=0.4,
        labels={"request_type": "Request Type", "count": "Count"},
        color_discrete_sequence=BRAND_COLORS,
        height=CHART_HEIGHT,
    )
    fig_type.update_layout(margin={"l": 10, "t": 10, "b": 10, "r": 10})
    st.plotly_chart(fig_type, use_container_width=True)
