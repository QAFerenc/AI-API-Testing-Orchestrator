from langgraph.graph import StateGraph, START, END

from agents import (
    planner_agent,
    fault_injection_agent,
    executor_agent,
    route_after_execution
)

from autonomous_agents import (
    AutonomousTestState,
    initial_state_8,
    autonomous_bug_analyzer,
    autonomous_correction_agent,
    autonomous_validation_agent,
    autonomous_retry_agent,
    retry_evaluation_agent,
    autonomous_router,
    validation_router,
    autonomous_reporter_agent
)


def build_workflow():

    workflow = StateGraph(AutonomousTestState)

    # Register nodes

    workflow.add_node("planner", planner_agent)

    workflow.add_node(
        "fault_injection",
        fault_injection_agent
    )

    workflow.add_node("executor", executor_agent)

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
        autonomous_retry_agent
    )

    workflow.add_node(
        "retry_evaluation",
        retry_evaluation_agent
    )

    workflow.add_node(
        "reporter",
        autonomous_reporter_agent
    )

    # Initial execution

    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "fault_injection")
    workflow.add_edge("fault_injection", "executor")

    # Conditional routing

    workflow.add_conditional_edges(
        "executor",
        route_after_execution,
        {
            "bug_analyzer": "bug_analyzer",
            "reporter": "reporter"
        }
    )

    # Analysis and correction

    workflow.add_edge("bug_analyzer", "correction")
    workflow.add_edge("correction", "validation")

    # Validation routing

    workflow.add_conditional_edges(
        "validation",
        validation_router,
        {
            "retry": "retry",
            "reporter": "reporter"
        }
    )

    # Retry evaluation

    workflow.add_edge("retry", "retry_evaluation")

    # Autonomous feedback loop

    workflow.add_conditional_edges(
        "retry_evaluation",
        autonomous_router,
        {
            "bug_analyzer": "bug_analyzer",
            "reporter": "reporter"
        }
    )

    # Finish workflow

    workflow.add_edge("reporter", END)

    return workflow.compile()


app8 = build_workflow()
