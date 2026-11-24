from config import (
    ai_client,
    AI_MODELS,
    MAX_RETRIES
)

from api_mcp_server import mcp

from api_specification import (
    api_details,
    REFERENCE_EXPECTATIONS
)

from agents import (
    planner_agent,
    executor_agent,
    fault_injection_agent,
    route_after_execution,
    bug_analyzer_agent,
    correction_agent,
    validation_agent
)

from autonomous_agents import (
    AutonomousTestState,
    initial_state_8,
    autonomous_retry_agent,
    retry_evaluation_agent,
    autonomous_router,
    autonomous_bug_analyzer,
    autonomous_correction_agent,
    autonomous_validation_agent,
    validation_router,
    autonomous_reporter_agent
)

from workflow import (
    build_workflow,
    app8
)


def verify_environment():

    required = [
        "mcp",
        "ai_client",
        "api_details",
        "planner_agent",
        "executor_agent",
        "fault_injection_agent",
        "bug_analyzer_agent",
        "correction_agent",
        "validation_agent",
        "route_after_execution",
        "AutonomousTestState",
        "initial_state_8",
        "autonomous_retry_agent",
        "retry_evaluation_agent",
        "autonomous_router",
        "autonomous_bug_analyzer",
        "autonomous_correction_agent",
        "autonomous_validation_agent",
        "validation_router",
        "autonomous_reporter_agent",
        "app8"
    ]

    print("COMPLETE ENVIRONMENT VERIFICATION")
    print("=" * 50)

    missing = []

    for name in required:

        if name in globals():
            print(f"{name}: AVAILABLE")
        else:
            print(f"{name}: MISSING")
            missing.append(name)

    if missing:
        raise RuntimeError(
            f"Missing components: {missing}"
        )

    print("=" * 50)
    print("Available components:", len(required))
    print("SUCCESS: Complete environment restored!")



# TASK 9 PARALLEL COMPONENTS

from parallel_executor import (
    MAX_CONCURRENT_REQUESTS,
    execute_single_test,
    parallel_executor_agent
)

from parallel_autonomous_agents import (
    parallel_autonomous_retry_agent
)

from parallel_workflow import (
    build_parallel_workflow,
    app9
)

from parallel_branch_workflow import (
    build_parallel_branch_workflow,
    app9_parallel
)


def verify_parallel_environment():

    required_components = [
        "MAX_CONCURRENT_REQUESTS",
        "execute_single_test",
        "parallel_executor_agent",
        "parallel_autonomous_retry_agent",
        "build_parallel_workflow",
        "app9",
        "build_parallel_branch_workflow",
        "app9_parallel"
    ]

    print("TASK 9 ENVIRONMENT VERIFICATION")
    print("=" * 55)

    for component in required_components:

        assert component in globals(), (
            f"Missing component: {component}"
        )

        print(component, "| AVAILABLE")

    assert MAX_CONCURRENT_REQUESTS == 5

    assert app8 is not app9
    assert app9 is not app9_parallel
    assert app8 is not app9_parallel

    print("\nAvailable parallel components:",
          len(required_components))

    print("\nSUCCESS: Task 9 environment restored!")

# TASK 10 REPORTING COMPONENTS

from logging_config import log_event, LOG_FILE

from agent_logging import AgentLoggingCallback

from api_logging import current_execution_id

from error_logging import (
    classify_exception,
    log_exception,
    log_ai_model_failure,
    classify_api_result
)

from performance_metrics import (
    load_execution_logs,
    calculate_statistics,
    calculate_execution_metrics
)

from json_reporter import (
    build_json_report,
    save_json_report
)

from html_reporter import (
    build_html_report,
    save_html_report
)

from performance_visualization import (
    generate_performance_charts
)

from visual_reporter import (
    build_visual_html_report,
    save_visual_html_report
)

from orchestrator import run_orchestrator


def verify_reporting_environment():

    required_components = [
        "log_event",
        "LOG_FILE",
        "AgentLoggingCallback",
        "current_execution_id",
        "classify_exception",
        "log_exception",
        "log_ai_model_failure",
        "classify_api_result",
        "load_execution_logs",
        "calculate_statistics",
        "calculate_execution_metrics",
        "build_json_report",
        "save_json_report",
        "build_html_report",
        "save_html_report",
        "generate_performance_charts",
        "build_visual_html_report",
        "save_visual_html_report",
        "run_orchestrator"
    ]

    print("REPORTING ENVIRONMENT VERIFICATION")
    print("=" * 60)

    for component in required_components:

        available = component in globals()

        print(
            f"{component:35s}",
            "|",
            "AVAILABLE" if available else "MISSING"
        )

        assert available, component

    print(
        "\nVerified reporting components:",
        len(required_components)
    )

    print("\nSUCCESS: Reporting environment ready!")
