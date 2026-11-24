import json

from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

from performance_metrics import (
    calculate_execution_metrics,
    load_execution_logs
)

PROJECT_DIR = Path(__file__).resolve().parent

REPORT_DIR = PROJECT_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)


def test_passed(result):

    return (
        result["actual"] == result["expected"]
        and not result.get("error")
    )


def build_json_report(state, execution_id):

    original_results = state["results"]

    retry_history = state["retry_history"]

    latest_results = {
        result["path"]: result
        for result in original_results
    }

    original_failed_paths = {
        result["path"]
        for result in original_results
        if not test_passed(result)
    }

    for attempt in retry_history:

        for result in attempt["results"]:

            latest_results[result["path"]] = result

    final_results = list(latest_results.values())

    unresolved_results = [
        result for result in final_results
        if not test_passed(result)
    ]

    recovered_results = [
        result for result in final_results
        if result["path"] in original_failed_paths
        and test_passed(result)
    ]

    original_passed = sum(
        test_passed(result)
        for result in original_results
    )

    final_passed = sum(
        test_passed(result)
        for result in final_results
    )

    total_api_executions = (
        len(original_results)
        + sum(
            len(attempt["results"])
            for attempt in retry_history
        )
    )

    metrics = calculate_execution_metrics(
        execution_id
    )

    logs = load_execution_logs(execution_id)

    error_events = [
        entry for entry in logs
        if entry["event"] in {
            "ai_model_failed",
            "api_execution_error",
            "agent_failed",
            "workflow_failed"
        }
    ]

    error_categories = Counter(
        entry["data"].get(
            "error_category",
            entry["data"].get(
                "error_type",
                "UNKNOWN"
            )
        )
        for entry in error_events
    )

    return {

        "metadata": {
            "project": "AI API Testing Orchestrator",
            "schema_version": "1.0",
            "execution_id": execution_id,
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat()
        },

        "summary": {
            "status": (
                "FAILED" if unresolved_results
                else "PASSED" if final_results
                else "NO_TESTS"
            ),
            "original_tests": len(original_results),
            "original_passed": original_passed,
            "original_failed": (
                len(original_results) - original_passed
            ),
            "total_api_executions": total_api_executions,
            "final_passed": final_passed,
            "final_failed": len(unresolved_results),
            "recovered_tests": len(recovered_results),
            "unresolved_failures": len(unresolved_results),
            "retry_count": state["retry_count"],
            "max_retries": state["max_retries"],
            "stop_reason": state["stop_reason"],
            "final_pass_rate_percent": (
                final_passed / len(final_results) * 100
                if final_results else 0.0
            )
        },

        "original_test_results": original_results,

        "final_test_results": final_results,

        "ai_analysis": {
            "bug_analysis": state.get(
                "bug_analysis", ""
            ),
            "correction_proposals": state.get(
                "correction_proposals", []
            ),
            "validated_corrections": state.get(
                "validated_corrections", []
            )
        },

        "retry_history": retry_history,

        "recovered_results": recovered_results,

        "unresolved_results": unresolved_results,

        "performance": metrics,

        "error_summary": {
            "total_error_events": len(error_events),
            "categories": dict(error_categories),
            "ai_model_failures": sum(
                entry["event"] == "ai_model_failed"
                for entry in error_events
            ),
            "api_execution_errors": sum(
                entry["event"] == "api_execution_error"
                for entry in error_events
            ),
            "agent_failures": sum(
                entry["event"] == "agent_failed"
                for entry in error_events
            ),
            "workflow_failures": sum(
                entry["event"] == "workflow_failed"
                for entry in error_events
            )
        }
    }


def save_json_report(report):

    execution_id = report["metadata"]["execution_id"]

    report_file = (
        REPORT_DIR / f"test_report_{execution_id}.json"
    )

    report_file.write_text(
        json.dumps(
            report,
            indent=4,
            ensure_ascii=False,
            allow_nan=False
        ) + chr(10),
        encoding="utf-8"
    )

    return report_file
