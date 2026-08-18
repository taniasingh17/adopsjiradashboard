# Ad Ops - EA | Jira Ticket Dashboard

A real-time Streamlit dashboard for the MiQ Ad Ops team, showing ticket metrics from the *TKTS* Jira Service Management project.

---

## Features

- *Ticket counts* grouped by assignee and status
- *Request type distribution* (donut chart)
- *KPI metrics* — total tickets, done count, completion rate
- *Time filters* — Today, This Week, This Month, or a custom date range
- *Date mode* — filter by Created or Updated date
- *Auto-refresh* every 2 minutes
- *Brand colours* from the MiQ palette

---

## Project Structure


.
├── app.py               # Streamlit UI
├── jira_client.py       # Jira REST API calls
├── data_processor.py    # Aggregation and JQL helpers
├── config.py            # Environment variable loading
├── requirements.txt
├── logo.png
└── tests/
    ├── test_jira_client.py
    └── test_data_processor.py


---

## Local Setup

*1. Clone the repo*

bash
git clone https://github.com/taniasingh17/adopsjiradashboard.git
cd adopsjiradashboard


*2. Install dependencies*

bash
pip install -r requirements.txt


*3. Create a .env file* in the project root:

env
JIRA_URL=https://mediaiq.atlassian.net
JIRA_EMAIL=your-email@mediaiq.com
JIRA_API_TOKEN=your-api-token


> Get your API token at: https://id.atlassian.com/manage-profile/security/api-tokens

*4. Run the app*

bash
streamlit run app.py


---

## Running Tests

bash
pytest tests/ -v


---

## Deploying to Streamlit Community Cloud

1. Push the repo to GitHub (already done).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click *New app* and select:
   - Repository: taniasingh17/adopsjiradashboard
   - Branch: main
   - Main file: app.py
4. Open *Settings → Secrets* and add:

toml
JIRA_URL = "https://mediaiq.atlassian.net"
JIRA_EMAIL = "your-email@mediaiq.com"
JIRA_API_TOKEN = "your-api-token"


5. Click *Deploy*.

---

## Environment Variables

| Variable | Description |
|---|---|
| JIRA_URL | Base URL of your Jira instance, e.g. https://mediaiq.atlassian.net |
| JIRA_EMAIL | Email address tied to your Atlassian account |
| JIRA_API_TOKEN | Atlassian API token (never commit this) |

---

Made with ❤️ by Tania Singh — MiQ AdOps team
