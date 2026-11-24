from pathlib import Path

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

from json_reporter import REPORT_DIR
from performance_metrics import load_execution_logs


def create_figure(width=10, height=5):

    figure = Figure(figsize=(width, height))

    FigureCanvasAgg(figure)

    axis = figure.add_subplot(111)

    return figure, axis


def save_figure(figure, path):

    figure.tight_layout()

    figure.savefig(
        path,
        dpi=150,
        bbox_inches="tight"
    )

    figure.clear()

    return path


def create_test_results_chart(report, output_dir):

    summary = report["summary"]

    figure, axis = create_figure()

    positions = [0, 1]

    passed = [
        summary["original_passed"],
        summary["final_passed"]
    ]

    failed = [
        summary["original_failed"],
        summary["final_failed"]
    ]

    passed_bars = axis.bar(
        [x - 0.18 for x in positions],
        passed,
        width=0.36,
        label="Passed"
    )

    failed_bars = axis.bar(
        [x + 0.18 for x in positions],
        failed,
        width=0.36,
        label="Failed"
    )

    axis.bar_label(passed_bars, padding=3)

    axis.bar_label(failed_bars, padding=3)

    axis.set_xticks(
        positions,
        ["Original results", "Final results"]
    )

    axis.set_ylabel("Number of tests")

    axis.set_title(
        "Original vs Final API Test Results"
    )

    axis.set_ylim(
        0,
        max(passed + failed + [1]) * 1.25
    )

    axis.legend()

    axis.grid(axis="y", alpha=0.2)

    return save_figure(
        figure,
        output_dir / "test_results.png"
    )


def create_agent_duration_chart(report, output_dir):

    metrics = report["performance"]["agent_metrics"]

    sorted_agents = sorted(
        metrics.items(),
        key=lambda item: item[1]["total"]
    )

    names = [
        item[0] for item in sorted_agents
    ]

    durations = [
        item[1]["total"] for item in sorted_agents
    ]

    figure, axis = create_figure(10, 6)

    bars = axis.barh(names, durations)

    axis.bar_label(
        bars,
        labels=[
            f"{duration:.3f} s"
            for duration in durations
        ],
        padding=4
    )

    axis.set_xlabel("Accumulated duration (seconds)")

    axis.set_title("LangGraph Agent Execution Durations")

    axis.set_xlim(
        0,
        max(durations + [0.01]) * 1.25
    )

    axis.grid(axis="x", alpha=0.2)

    return save_figure(
        figure,
        output_dir / "agent_durations.png"
    )


def create_api_duration_chart(report, output_dir):

    execution_id = report["metadata"]["execution_id"]

    logs = load_execution_logs(execution_id)

    requests = [
        entry["data"]
        for entry in logs
        if entry["event"] == "api_request_completed"
    ]

    labels = [
        f"{index + 1}. {request['path']}"
        for index, request in enumerate(requests)
    ]

    durations = [
        request["duration_seconds"] * 1000
        for request in requests
    ]

    figure, axis = create_figure(10, 6)

    bars = axis.barh(labels, durations)

    axis.bar_label(
        bars,
        labels=[
            f"{duration:.1f} ms"
            for duration in durations
        ],
        padding=4
    )

    axis.invert_yaxis()

    axis.set_xlabel("MCP execution duration (ms)")

    axis.set_title("Individual API Request Durations")

    axis.set_xlim(
        0,
        max(durations + [1]) * 1.25
    )

    axis.grid(axis="x", alpha=0.2)

    return save_figure(
        figure,
        output_dir / "api_durations.png"
    )


def create_recovery_chart(report, output_dir):

    summary = report["summary"]

    recovered = summary["recovered_tests"]

    original_failed = summary["original_failed"]

    not_recovered = original_failed - recovered

    figure, axis = create_figure(7, 5)

    if original_failed > 0:

        axis.pie(
            [recovered, not_recovered],
            labels=["Recovered", "Not recovered"],
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops={"width": 0.4}
        )

        recovery_rate = (
            recovered / original_failed * 100
        )

        axis.text(
            0,
            0,
            f"{recovery_rate:.0f}%",
            ha="center",
            va="center",
            fontsize=24,
            fontweight="bold"
        )

    else:

        axis.text(
            0.5,
            0.5,
            "No original failures",
            ha="center",
            va="center",
            transform=axis.transAxes
        )

        axis.axis("off")

    axis.set_title("Autonomous Test Recovery")

    return save_figure(
        figure,
        output_dir / "test_recovery.png"
    )


def generate_performance_charts(report):

    execution_id = report["metadata"]["execution_id"]

    output_dir = (
        REPORT_DIR / execution_id / "charts"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return {
        "test_results":
            create_test_results_chart(
                report, output_dir
            ),

        "agent_durations":
            create_agent_duration_chart(
                report, output_dir
            ),

        "api_durations":
            create_api_duration_chart(
                report, output_dir
            ),

        "test_recovery":
            create_recovery_chart(
                report, output_dir
            )
    }
