import json
import math
import statistics

from logging_config import LOG_FILE


def load_execution_logs(execution_id):

    with LOG_FILE.open("r", encoding="utf-8") as file:

        entries = [
            json.loads(line)
            for line in file
            if line.strip()
        ]

    return [
        entry for entry in entries
        if entry.get("data", {}).get("execution_id")
        == execution_id
    ]


def calculate_statistics(durations):

    if not durations:

        return {
            "count": 0,
            "total": 0.0,
            "average": None,
            "minimum": None,
            "maximum": None,
            "median": None,
            "p95": None,
            "standard_deviation": None
        }

    ordered = sorted(durations)

    p95_index = max(
        0,
        math.ceil(0.95 * len(ordered)) - 1
    )

    return {
        "count": len(durations),
        "total": sum(durations),
        "average": statistics.mean(durations),
        "minimum": min(durations),
        "maximum": max(durations),
        "median": statistics.median(durations),
        "p95": ordered[p95_index],
        "standard_deviation":
            statistics.pstdev(durations)
    }


def calculate_execution_metrics(execution_id):

    entries = load_execution_logs(execution_id)

    if not entries:
        raise ValueError("Execution ID not found")

    agent_entries = [
        entry for entry in entries
        if entry["event"] in {
            "agent_completed",
            "agent_failed"
        }
    ]

    api_entries = [
        entry for entry in entries
        if entry["event"] == "api_request_completed"
    ]

    workflow_entries = [
        entry for entry in entries
        if entry["event"] in {
            "workflow_completed",
            "workflow_failed"
        }
    ]

    agent_metrics = {}

    for entry in agent_entries:

        agent = entry["agent"]

        agent_metrics.setdefault(agent, []).append(
            entry["data"]["duration_seconds"]
        )

    agent_metrics = {
        agent: calculate_statistics(durations)
        for agent, durations in agent_metrics.items()
    }

    api_durations = [
        entry["data"]["duration_seconds"]
        for entry in api_entries
    ]

    agent_durations = [
        entry["data"]["duration_seconds"]
        for entry in agent_entries
    ]

    slowest_agent = max(
        agent_entries,
        key=lambda entry:
            entry["data"]["duration_seconds"],
        default=None
    )

    slowest_request = max(
        api_entries,
        key=lambda entry:
            entry["data"]["duration_seconds"],
        default=None
    )

    workflow_data = (
        workflow_entries[-1]["data"]
        if workflow_entries
        else {}
    )

    return {
        "execution_id": execution_id,
        "workflow_duration_seconds":
            workflow_data.get("duration_seconds"),
        "retry_count":
            workflow_data.get("retry_count"),
        "stop_reason":
            workflow_data.get("stop_reason"),
        "agent_statistics":
            calculate_statistics(agent_durations),
        "agent_metrics": agent_metrics,
        "api_statistics":
            calculate_statistics(api_durations),
        "slowest_agent": {
            "name": slowest_agent["agent"],
            "duration_seconds":
                slowest_agent["data"]["duration_seconds"]
        } if slowest_agent else None,
        "slowest_api_request": {
            "path": slowest_request["data"]["path"],
            "duration_seconds":
                slowest_request["data"]["duration_seconds"]
        } if slowest_request else None
    }
