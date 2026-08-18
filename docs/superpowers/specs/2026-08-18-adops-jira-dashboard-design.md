# Ad Ops Jira Dashboard — Design Spec

**Date:** 2026-08-18
**Status:** Approved

## Overview

A Streamlit web app that provides real-time visibility into Jira ticket distribution and completion rates for the "Ad Ops - EA" service desk queue (`TKTS` project, queue ID 37). The dashboard surfaces workload per assignee, request type trends, and individual status breakdowns across configurable time periods.

---

## Architecture

### File Structure

```
AdOps Jira Dashboard/
├── app.py                  # Streamlit UI — layout, filters, charts
├── jira_client.py          # Jira REST API calls — auth, issue fetching
├── data_processor.py       # Aggregation — group by assignee, status, request type
├── config.py               # Env var loading and validation
├── requirements.txt        # pinned dependencies
├── .env                    # Local secrets (gitignored)
└── .env.example            # Placeholder env file (committed)
```

### Data Flow

1. `config.py` reads and validates env vars → exposes `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
2. `jira_client.py` builds JQL queries dynamically and calls `GET /rest/api/3/search` → returns raw issue list
3. `data_processor.py` transforms raw issues into pandas DataFrames grouped by assignee, status, and request type
4. `app.py` renders sidebar controls → triggers data fetch → renders Plotly charts

---

## Jira Integration

### Authentication
- Basic Auth: `JIRA_EMAIL` + `JIRA_API_TOKEN` (Base64-encoded, per Atlassian docs)
- Base URL: `https://mediaiq.atlassian.net`
- All requests include `Accept: application/json` header

### JQL Query Pattern

JSM queues don't expose a `queue` JQL clause directly. Instead:

1. **Fetch queue base JQL** once at startup via:
   `GET /rest/servicedeskapi/servicedesk/{serviceDeskId}/queue/37`
   This returns the queue's saved JQL filter (e.g. `project = TKTS AND ...`).

2. **Append time filter** to the base JQL:
   ```jql
   {base_jql} AND {date_field} >= {start_date}
   ```

- `date_field`: `created` or `updated` (toggled by user)
- `start_date`: `startOfDay()`, `startOfWeek()`, or `startOfMonth()` (based on time period selection)
- `serviceDeskId` resolved via `GET /rest/servicedeskapi/servicedesk` filtered by `projectKey = TKTS`
- Results paginated via `startAt` + `maxResults=100` until all issues fetched
- Queue base JQL cached with `@st.cache_data(ttl=3600)` — it rarely changes

### Fields Fetched Per Issue
- `assignee.displayName`
- `status.name`
- `issuetype.name` (used as request type)
- `created`, `updated`

---

## UI Layout

### Sidebar Controls
| Control | Type | Values |
|---------|------|--------|
| Time period | Radio | Today / This Week / This Month |
| Date mode | Toggle | Created / Updated |
| Refresh | Button | Clears cache, re-fetches |

### Main Panel

**1. KPI Row (3 stat tiles)**
- Total tickets in period
- Total "Done" tickets
- Completion rate (%)

**2. Tickets by Assignee**
- Horizontal bar chart (Plotly), sorted descending by count
- Shows total ticket count per assignee for the selected period/mode

**3. Status Breakdown by Assignee**
- Stacked horizontal bar chart
- Each bar segment = individual status (Open, In Progress, Waiting for Customer, Done, etc.)
- Colors assigned per status name, consistent across the session

**4. Request Type Distribution**
- Donut chart (Plotly)
- Segments = ticket count per `issuetype.name`

---

## Caching

- `@st.cache_data(ttl=300)` on the API fetch function — auto-refreshes every 5 minutes
- Refresh button calls `st.cache_data.clear()` then triggers re-run

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Missing env var | `st.error("JIRA_API_TOKEN not set — check your .env file")` + stop |
| 401 / 403 from Jira | `st.error("Authentication failed — check credentials")` |
| 404 from Jira | `st.error("Queue or project not found")` |
| Network timeout | 10s request timeout; `st.error("Request timed out — Jira may be unreachable")` |
| No tickets found | `st.info("No tickets found for this period")` — charts hidden |

---

## Dependencies

```
streamlit>=1.35.0
pandas>=2.0.0
plotly>=5.20.0
requests>=2.31.0
python-dotenv>=1.0.0
```

---

## Deployment

### Local Development
```bash
pip install -r requirements.txt
cp .env.example .env   # fill in credentials
streamlit run app.py
```

### Streamlit Community Cloud
- Connect GitHub repo → select `app.py` as entry point
- Set secrets in Streamlit Cloud UI (Settings → Secrets):
  ```
  JIRA_URL=https://mediaiq.atlassian.net
  JIRA_EMAIL=your@email.com
  JIRA_API_TOKEN=your_token_here
  ```
- `python-dotenv` is only used locally; on Streamlit Cloud the env vars are injected directly

### Environment Variables

| Variable | Description |
|----------|-------------|
| `JIRA_URL` | Jira base URL, e.g. `https://mediaiq.atlassian.net` |
| `JIRA_EMAIL` | Atlassian account email |
| `JIRA_API_TOKEN` | API token from Atlassian account settings |

---

## Out of Scope

- Ticket-level drill-down view
- SLA tracking
- Notifications or alerting
- Authentication/login for the dashboard itself
