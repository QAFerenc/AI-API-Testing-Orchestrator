from langgraph.graph import StateGraph, START, END

from agents import (
    planner_agent,
    fault_injection_agent,
    route_after_execution
)

from autonomous_agents import (
    AutonomousTestState,
    autonomous_bug_analyzer,
    autonomous_correction_agent,
    autonomous_validation_agent,
    validation_router,
    retry_evaluation_agent,
    autonomous_router,
    autonomous_reporter_agent
)

from parallel_executor import parallel_executor_agent

from parallel_autonomous_agents import (
    parallel_autonomous_retry_agent
)


def build_parallel_workflow():

    workflow = StateGraph(AutonomousTestState)

    # Register agents

    workflow.add_node(
        "planner",
        planner_agent
    )

    workflow.add_node(
        "fault_injection",
        fault_injection_agent
    )

    workflow.add_node(
        "executor",
        parallel_executor_agent
    )

    workflow.add_node(
        "bug_analyzer",
        autonomous_bug_analyzer
    )

    workflow.add_node(
        "correction",
        autonomous_correction_agent
    )

    workflow.add_node(
        "validation",
        autonomous_validation_agent
    )

    workflow.add_node(
        "retry",
        parallel_autonomous_retry_agent
    )

    workflow.add_node(
        "retry_evaluation",
        retry_evaluation_agent
    )

    workflow.add_node(
        "reporter",
        autonomous_reporter_agent
    )

    # Define workflow edges

    workflow.add_edge(
        START,
        "planner"
    )

    workflow.add_edge(
        "planner",
        "fault_injection"
    )

    workflow.add_edge(
        "fault_injection",
        "executor"
    )

    workflow.add_conditional_edges(
        "executor",
        route_after_execution,
        {
            "bug_analyzer": "bug_analyzer",
            "reporter": "reporter"
        }
    )

    workflow.add_edge(
        "bug_analyzer",
        "correction"
    )

    workflow.add_edge(
        "correction",
        "validation"
    )

    workflow.add_conditional_edges(
        "validation",
        validation_router,
        {
            "retry": "retry",
            "reporter": "reporter"
        }
    )

    workflow.add_edge(
        "retry",
        "retry_evaluation"
    )

    workflow.add_conditional_edges(
        "retry_evaluation",
        autonomous_router,
        {
            "bug_analyzer": "bug_analyzer",
            "reporter": "reporter"
        }
    )

    workflow.add_edge(
        "reporter",
        END
    )

    return workflow.compile()


app9 = build_parallel_workflow()
