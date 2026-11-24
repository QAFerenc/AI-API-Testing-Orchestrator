import asyncio
import copy
import time
import logging

from autonomous_agents import initial_state_8

from parallel_branch_workflow import (
    build_parallel_branch_workflow
)

from agent_logging import AgentLoggingCallback

from api_logging import current_execution_id

from logging_config import log_event

from error_logging import log_exception

from json_reporter import (
    build_json_report,
    save_json_report
)

from html_reporter import save_html_report

from performance_visualization import (
    generate_performance_charts
)

from visual_reporter import save_visual_html_report


async def run_orchestrator(
    initial_state=None,
    timeout=300,
    recursion_limit=50
):

    if initial_state is None:

        initial_state = initial_state_8

    state = copy.deepcopy(initial_state)

    agent_logger = AgentLoggingCallback()

    execution_id = agent_logger.execution_id

    context_token = current_execution_id.set(
        execution_id
    )

    workflow_start = time.perf_counter()

    try:

        log_event(
            logging.INFO,
            "Integrated workflow started",
            agent="Orchestrator",
            event="workflow_started",
            execution_id=execution_id
        )

        try:

            app = build_parallel_branch_workflow()

            final_state = await asyncio.wait_for(
                app.ainvoke(
                    state,
                    config={
                        "recursion_limit":
                            recursion_limit,
                        "callbacks": [agent_logger]
                    }
                ),
                timeout=timeout
            )

        except Exception as error:

            log_exception(
                error,
                agent="Orchestrator",
                event="workflow_failed",
                execution_id=execution_id,
                duration_seconds=(
                    time.perf_counter()
                    - workflow_start
                )
            )

            raise

        workflow_duration = (
            time.perf_counter() - workflow_start
        )

        log_event(
            logging.INFO,
            "Integrated workflow completed",
            agent="Orchestrator",
            event="workflow_completed",
            execution_id=execution_id,
            duration_seconds=workflow_duration,
            retry_count=final_state["retry_count"],
            stop_reason=final_state["stop_reason"]
        )

        reporting_start = time.perf_counter()

        log_event(
            logging.INFO,
            "Report generation started",
            agent="Reporting",
            event="reporting_started",
            execution_id=execution_id
        )

        try:

            report = build_json_report(
                final_state,
                execution_id
            )

            json_path = save_json_report(report)

            html_path = save_html_report(report)

            chart_paths = generate_performance_charts(
                report
            )

            visual_html_path = save_visual_html_report(
                report,
                chart_paths
            )

        except Exception as error:

            log_exception(
                error,
                agent="Reporting",
                event="reporting_failed",
                execution_id=execution_id,
                duration_seconds=(
                    time.perf_counter()
                    - reporting_start
                )
            )

            raise

        reporting_duration = (
            time.perf_counter() - reporting_start
        )

        total_duration = (
            time.perf_counter() - workflow_start
        )

        log_event(
            logging.INFO,
            "Report generation completed",
            agent="Reporting",
            event="reporting_completed",
            execution_id=execution_id,
            duration_seconds=reporting_duration,
            generated_files=3 + len(chart_paths)
        )

        log_event(
            logging.INFO,
            "Orchestration completed",
            agent="Orchestrator",
            event="orchestration_completed",
            execution_id=execution_id,
            duration_seconds=total_duration,
            test_status=report["summary"]["status"]
        )

        return {
            "execution_id": execution_id,
            "status": report["summary"]["status"],
            "final_state": final_state,
            "report": report,
            "workflow_duration_seconds":
                workflow_duration,
            "reporting_duration_seconds":
                reporting_duration,
            "total_duration_seconds":
                total_duration,
            "artifacts": {
                "json_report": json_path,
                "html_report": html_path,
                "visual_html_report": visual_html_path,
                "charts": chart_paths
            }
        }

    finally:

        current_execution_id.reset(context_token)
