import base64

from html import escape

from json_reporter import REPORT_DIR

from html_reporter import build_html_report

from performance_visualization import (
    generate_performance_charts
)


def encode_chart(path):

    return base64.b64encode(
        path.read_bytes()
    ).decode("ascii")


def build_visual_html_report(report, chart_paths):

    html_content = build_html_report(report)

    chart_sections = []

    for name, path in chart_paths.items():

        title = escape(
            name.replace("_", " ").title(),
            quote=True
        )

        encoded_image = encode_chart(path)

        chart_sections.append(f"""
        <figure style="margin:24px 0;">

            <h3>{title}</h3>

            <img
                src="data:image/png;base64,{encoded_image}"
                alt="{title}"
                style="width:100%;max-width:1000px;height:auto;"
            >

        </figure>
        """)

    visualization_section = (
        '<section id="visualizations">'
        '<h2>Performance Visualizations</h2>'
        + "".join(chart_sections)
        + '</section>'
    )

    assert html_content.count("</main>") == 1

    html_content = html_content.replace(
        "</main>",
        visualization_section + "</main>",
        1
    )

    assert html_content.count("</nav>") == 1

    html_content = html_content.replace(
        "</nav>",
        '<a href="#visualizations">'
        'Visualizations</a></nav>',
        1
    )

    return html_content


def save_visual_html_report(report, chart_paths=None):

    if chart_paths is None:

        chart_paths = generate_performance_charts(
            report
        )

    execution_id = report["metadata"]["execution_id"]

    report_path = (
        REPORT_DIR
        / f"visual_test_report_{execution_id}.html"
    )

    html_content = build_visual_html_report(
        report,
        chart_paths
    )

    report_path.write_text(
        html_content,
        encoding="utf-8"
    )

    return report_path
