import pandas as pd

_PERIOD_JQL = {
    "today": "startOfDay()",
    "week": "startOfWeek()",
    "month": "startOfMonth()",
}


def build_jql(base_jql: str, date_field: str, period: str) -> str:
    time_clause = f"{date_field} >= {_PERIOD_JQL[period]}"
    order_idx = base_jql.upper().find(" ORDER BY ")
    if order_idx != -1:
        return f"{base_jql[:order_idx]} AND {time_clause}{base_jql[order_idx:]}"
    return f"{base_jql} AND {time_clause}"


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


def build_jql_range(base_jql: str, date_field: str, start_date, end_date) -> str:
    clause = f'{date_field} >= "{start_date}" AND {date_field} <= "{end_date}"'
    order_idx = base_jql.upper().find(" ORDER BY ")
    if order_idx != -1:
        return f"{base_jql[:order_idx]} AND {clause}{base_jql[order_idx:]}"
    return f"{base_jql} AND {clause}"


_DONE_STATUSES = {"done", "resolved", "closed", "complete", "completed"}


def compute_kpis(issues: list) -> dict:
    total = len(issues)
    done = sum(1 for i in issues if _status_name(i).lower() in _DONE_STATUSES)
    rate = round(done / total * 100, 1) if total > 0 else 0.0
    return {"total": total, "done": done, "completion_rate": rate}
