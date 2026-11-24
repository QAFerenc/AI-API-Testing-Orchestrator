import copy
import pytest

import json_reporter
import html_reporter

from autonomous_agents import initial_state_8
from json_reporter import build_json_report
from performance_metrics import calculate_statistics
from visual_reporter import encode_chart


@pytest.fixture
def report_state():

    state = copy.deepcopy(initial_state_8)

    state["results"] = [
        {
            "path": "/posts/1",
            "expected": 404,
            "actual": 200,
            "error": None
        },
        {
            "path": "/users/1",
            "expected": 200,
            "actual": 200,
            "error": None
        }
    ]

    return state


@pytest.fixture
def mock_metrics(monkeypatch):

    monkeypatch.setattr(
        json_reporter,
        "calculate_execution_metrics",
        lambda execution_id: {
            "execution_id": execution_id
        }
    )

    monkeypatch.setattr(
        json_reporter,
        "load_execution_logs",
        lambda execution_id: []
    )


def test_failed_report(report_state, mock_metrics):

    report = build_json_report(
        report_state,
        "regression-test"
    )

    summary = report["summary"]

    assert summary["status"] == "FAILED"
    assert summary["original_tests"] == 2
    assert summary["original_failed"] == 1
    assert summary["unresolved_failures"] == 1


def test_recovered_report(report_state, mock_metrics):

    report_state["retry_count"] = 1

    report_state["retry_history"] = [
        {
            "attempt": 1,
            "test_cases": [
                {
                    "path": "/posts/1",
                    "expected_status": 200
                }
            ],
            "results": [
                {
                    "path": "/posts/1",
                    "expected": 200,
                    "actual": 200,
                    "error": None
                }
            ]
        }
    ]

    report = build_json_report(
        report_state,
        "regression-test"
    )

    summary = report["summary"]

    assert summary["status"] == "PASSED"
    assert summary["original_tests"] == 2
    assert summary["total_api_executions"] == 3
    assert summary["recovered_tests"] == 1
    assert summary["unresolved_failures"] == 0
    assert summary["final_pass_rate_percent"] == 100.0


def test_empty_report(mock_metrics):

    state = copy.deepcopy(initial_state_8)

    report = build_json_report(
        state,
        "empty-regression-test"
    )

    assert report["summary"]["status"] == "NO_TESTS"

    assert report["summary"]["final_pass_rate_percent"] == 0.0


def test_html_escaping():

    result = html_reporter.safe(
        "<script>alert(1)</script>"
    )

    assert "<script>" not in result
    assert "&lt;script&gt;" in result


def test_html_missing_value():

    assert html_reporter.safe(None) == "N/A"


def test_single_duration_statistics():

    result = calculate_statistics([2.5])

    assert result["count"] == 1
    assert result["average"] == 2.5
    assert result["p95"] == 2.5
    assert result["standard_deviation"] == 0.0


def test_json_report_persistence(
    report_state,
    mock_metrics,
    monkeypatch,
    tmp_path
):

    import json

    monkeypatch.setattr(
        json_reporter,
        "REPORT_DIR",
        tmp_path
    )

    report = build_json_report(
        report_state,
        "persistence-test"
    )

    path = json_reporter.save_json_report(report)

    assert path.exists()

    saved_report = json.loads(
        path.read_text(encoding="utf-8")
    )

    assert saved_report == report
