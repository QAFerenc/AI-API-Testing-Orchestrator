from pathlib import Path
from html import escape

from json_reporter import REPORT_DIR


def safe(value):

    if value is None:
        return "N/A"

    return escape(str(value), quote=True)


def format_seconds(value):

    if value is None:
        return "N/A"

    return f"{value:.3f} s"


def result_passed(result):

    return (
        result["actual"] == result["expected"]
        and not result.get("error")
    )


def render_test_table(results):

    rows = []

    for result in results:

        passed = result_passed(result)

        status = "PASS" if passed else "FAIL"

        css_class = "passed" if passed else "failed"

        rows.append(f"""
        <tr>
            <td>{safe(result["path"])}</td>
            <td>{safe(result["expected"])}</td>
            <td>{safe(result["actual"])}</td>
            <td class="{css_class}">{status}</td>
            <td>{safe(result.get("error") or "-")}</td>
        </tr>
        """)

    if not rows:

        rows.append(
            '<tr><td colspan="5">No results</td></tr>'
        )

    return """
    <table>
        <thead>
            <tr>
                <th>API path</th>
                <th>Expected</th>
                <th>Actual</th>
                <th>Status</th>
                <th>Error</th>
            </tr>
        </thead>
        <tbody>
    """ + "".join(rows) + """
        </tbody>
    </table>
    """


def render_agent_table(agent_metrics):

    rows = []

    sorted_agents = sorted(
        agent_metrics.items(),
        key=lambda item: item[1]["total"],
        reverse=True
    )

    for agent, data in sorted_agents:

        rows.append(f"""
        <tr>
            <td>{safe(agent)}</td>
            <td>{data["count"]}</td>
            <td>{format_seconds(data["average"])}</td>
            <td>{format_seconds(data["total"])}</td>
        </tr>
        """)

    return """
    <table>
        <thead>
            <tr>
                <th>Agent</th>
                <th>Executions</th>
                <th>Average duration</th>
                <th>Total duration</th>
            </tr>
        </thead>
        <tbody>
    """ + "".join(rows) + """
        </tbody>
    </table>
    """


def render_retry_history(retry_history):

    if not retry_history:

        return "<p>No retries performed.</p>"

    sections = []

    for attempt in retry_history:

        sections.append(
            f'<h3>Retry attempt '
            f'{safe(attempt["attempt"])}</h3>'
            + render_test_table(attempt["results"])
        )

    return "".join(sections)


def render_corrections(corrections):

    if not corrections:

        return "<p>No validated corrections.</p>"

    rows = []

    for correction in corrections:

        rows.append(f"""
        <tr>
            <td>{safe(correction.get("path"))}</td>
            <td>{safe(correction.get("expected_status"))}</td>
            <td>{safe(correction.get("reason"))}</td>
        </tr>
        """)

    return """
    <table>
        <thead>
            <tr>
                <th>API path</th>
                <th>Corrected expectation</th>
                <th>Reason</th>
            </tr>
        </thead>
        <tbody>
    """ + "".join(rows) + """
        </tbody>
    </table>
    """


def build_html_report(report):

    metadata = report["metadata"]

    summary = report["summary"]

    performance = report["performance"]

    api_stats = performance["api_statistics"]

    errors = report["error_summary"]

    analysis = report["ai_analysis"]

    status = summary["status"]

    status_class = (
        "passed" if status == "PASSED"
        else "failed" if status == "FAILED"
        else "neutral"
    )

    kpis = [
        ("Original tests", summary["original_tests"]),
        ("Final passed", summary["final_passed"]),
        ("Original failures", summary["original_failed"]),
        ("Recovered tests", summary["recovered_tests"]),
        ("Unresolved failures", summary["unresolved_failures"]),
        ("Retry attempts", summary["retry_count"]),
        (
            "Final pass rate",
            f'{summary["final_pass_rate_percent"]:.1f}%'
        ),
        (
            "Workflow duration",
            format_seconds(
                performance["workflow_duration_seconds"]
            )
        )
    ]

    kpi_html = "".join(
        f"""
        <div class="kpi">
            <div class="label">{safe(label)}</div>
            <div class="value">{safe(value)}</div>
        </div>
        """
        for label, value in kpis
    )

    api_rows = "".join(
        f"""
        <tr>
            <td>{safe(name.replace("_", " ").title())}</td>
            <td>{
                safe(value) if name == "count"
                else format_seconds(value)
            }</td>
        </tr>
        """
        for name, value in api_stats.items()
    )

    error_rows = "".join(
        f"""
        <tr>
            <td>{safe(name.replace("_", " ").title())}</td>
            <td>{safe(value)}</td>
        </tr>
        """
        for name, value in errors.items()
        if name != "categories"
    )

    category_rows = "".join(
        f"<li>{safe(name)}: {safe(count)}</li>"
        for name, count in errors["categories"].items()
    ) or "<li>No classified exception events</li>"

    slowest_agent = performance.get("slowest_agent") or {}

    slowest_request = (
        performance.get("slowest_api_request") or {}
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>AI API Testing Orchestrator - Test Report</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: #f1f5f9;
    color: #1e293b;
    font-family: Arial, Helvetica, sans-serif;
    line-height: 1.5;
}}

header {{
    background: #0f172a;
    color: white;
    padding: 32px;
}}

header h1 {{
    margin: 0 0 10px;
}}

header p {{
    margin: 5px 0;
    overflow-wrap: anywhere;
}}

nav {{
    padding: 16px;
    background: white;
    text-align: center;
}}

nav a {{
    display: inline-block;
    margin: 6px 10px;
    color: #2563eb;
    text-decoration: none;
}}

main {{
    max-width: 1200px;
    margin: auto;
    padding: 24px;
}}

section {{
    background: white;
    padding: 24px;
    margin-bottom: 24px;
    border-radius: 10px;
    box-shadow: 0 2px 6px #0000000d;
    overflow-x: auto;
}}

h2 {{
    margin-top: 0;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 12px;
}}

.kpi-grid {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(170px, 1fr));
    gap: 16px;
}}

.kpi {{
    padding: 18px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #f8fafc;
}}

.label {{
    font-size: 13px;
    color: #64748b;
}}

.value {{
    font-size: 28px;
    font-weight: bold;
    margin-top: 8px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}}

th, td {{
    text-align: left;
    padding: 12px;
    border-bottom: 1px solid #e2e8f0;
    overflow-wrap: anywhere;
}}

th {{
    background: #e2e8f0;
}}

tr:nth-child(even) {{
    background: #f8fafc;
}}

.passed {{
    color: #15803d;
    font-weight: bold;
}}

.failed {{
    color: #b91c1c;
    font-weight: bold;
}}

.neutral {{
    color: #475569;
    font-weight: bold;
}}

.status {{
    display: inline-block;
    padding: 8px 18px;
    border-radius: 20px;
    background: #f1f5f9;
    margin-top: 10px;
}}

.analysis {{
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    background: #f8fafc;
    padding: 18px;
    border-left: 4px solid #2563eb;
}}

footer {{
    text-align: center;
    color: #64748b;
    padding: 24px;
}}

@media print {{

    body {{
        background: white;
    }}

    nav {{
        display: none;
    }}

    section {{
        box-shadow: none;
        border: 1px solid #e2e8f0;
    }}
}}

</style>
</head>

<body>

<header>

<h1>AI API Testing Orchestrator</h1>

<p>Automated REST API Test Report</p>

<p>Execution ID: {safe(metadata["execution_id"])}</p>

<p>Generated: {safe(metadata["generated_at"])}</p>

<div class="status {status_class}">
    {safe(status)}
</div>

</header>

<nav>
    <a href="#summary">Summary</a>
    <a href="#original">Original tests</a>
    <a href="#final">Final results</a>
    <a href="#analysis">AI analysis</a>
    <a href="#retries">Retries</a>
    <a href="#performance">Performance</a>
    <a href="#errors">Errors</a>
</nav>

<main>

<section id="summary">

<h2>Execution Summary</h2>

<div class="kpi-grid">
    {kpi_html}
</div>

<p>
    <strong>Stop reason:</strong>
    {safe(summary["stop_reason"])}
</p>

</section>

<section id="original">

<h2>Original Test Results</h2>

{render_test_table(report["original_test_results"])}

</section>

<section id="final">

<h2>Final Test Results</h2>

{render_test_table(report["final_test_results"])}

<h3>Recovered Tests</h3>

{render_test_table(report["recovered_results"])}

<h3>Unresolved Failures</h3>

{render_test_table(report["unresolved_results"])}

</section>

<section id="analysis">

<h2>AI Bug Analysis</h2>

<div class="analysis">
{safe(analysis.get("bug_analysis") or "No analysis required.")}
</div>

<h3>Validated Corrections</h3>

{render_corrections(analysis["validated_corrections"])}

</section>

<section id="retries">

<h2>Autonomous Retry History</h2>

{render_retry_history(report["retry_history"])}

</section>

<section id="performance">

<h2>Performance Metrics</h2>

<h3>Agent Performance</h3>

{render_agent_table(performance["agent_metrics"])}

<h3>API Performance</h3>

<table>
    <thead>
        <tr>
            <th>Metric</th>
            <th>Value</th>
        </tr>
    </thead>
    <tbody>
        {api_rows}
    </tbody>
</table>

<h3>Performance Bottleneck Candidates</h3>

<p>
    <strong>Slowest agent:</strong>
    {safe(slowest_agent.get("name"))}
    ({format_seconds(slowest_agent.get("duration_seconds"))})
</p>

<p>
    <strong>Slowest API request:</strong>
    {safe(slowest_request.get("path"))}
    ({format_seconds(slowest_request.get("duration_seconds"))})
</p>

</section>

<section id="errors">

<h2>Error Summary</h2>

<table>
    <thead>
        <tr>
            <th>Error metric</th>
            <th>Count</th>
        </tr>
    </thead>
    <tbody>
        {error_rows}
    </tbody>
</table>

<h3>Error Categories</h3>

<ul>{category_rows}</ul>

</section>

</main>

<footer>
    AI API Testing Orchestrator |
    Report schema version {safe(metadata["schema_version"])}
</footer>

</body>
</html>
"""


def save_html_report(report):

    execution_id = report["metadata"]["execution_id"]

    report_path = (
        REPORT_DIR / f"test_report_{execution_id}.html"
    )

    html_content = build_html_report(report)

    report_path.write_text(
        html_content,
        encoding="utf-8"
    )

    return report_path
