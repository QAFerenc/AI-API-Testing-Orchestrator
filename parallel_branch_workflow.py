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


async def analysis_dispatch_agent(state):

    print("Analysis Dispatcher: starting parallel AI branches")

    return {}


def build_parallel_branch_workflow():

    workflow = StateGraph(AutonomousTestState)

    # Register nodes

    workflow.add_node("planner", planner_agent)

    workflow.add_node(
        "fault_injection",
        fault_injection_agent
    )

    workflow.add_node(
        "executor",
        parallel_executor_agent
    )

    workflow.add_node(
        "analysis_dispatch",
        analysis_dispatch_agent
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

    # Initial execution

    workflow.add_edge(START, "planner")

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
            "bug_analyzer": "analysis_dispatch",
            "reporter": "reporter"
        }
    )

    # Fan-out: start both independent AI agents

    workflow.add_edge(
        "analysis_dispatch",
        "bug_analyzer"
    )

    workflow.add_edge(
        "analysis_dispatch",
        "correction"
    )

    # Fan-in: wait for BOTH agents to finish

    workflow.add_edge(
        ["bug_analyzer", "correction"],
        "validation"
    )

    # Validation and retry

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
            "bug_analyzer": "analysis_dispatch",
            "reporter": "reporter"
        }
    )

    workflow.add_edge("reporter", END)

    return workflow.compile()


app9_parallel = build_parallel_branch_workflow()
