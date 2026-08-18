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


def test_build_jql_inserts_before_order_by():
    base = "project = TKTS AND resolved >= -1w ORDER BY resolved DESC"
    result = build_jql(base, "created", "today")
    assert result == "project = TKTS AND resolved >= -1w AND created >= startOfDay() ORDER BY resolved DESC"


def test_build_jql_order_by_case_insensitive():
    base = "project = TKTS order by created DESC"
    result = build_jql(base, "updated", "week")
    assert result == "project = TKTS AND updated >= startOfWeek() order by created DESC"


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


def test_compute_kpis_counts_resolved_and_closed_as_done():
    issues = [
        make_issue(status="Resolved"),
        make_issue(status="Closed"),
        make_issue(status="Open"),
    ]
    kpis = compute_kpis(issues)
    assert kpis["done"] == 2


def test_compute_kpis_empty_issues_returns_zeros():
    kpis = compute_kpis([])
    assert kpis["total"] == 0
    assert kpis["done"] == 0
    assert kpis["completion_rate"] == 0.0
