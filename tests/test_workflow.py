import asyncio
import copy
import pytest

from autonomous_agents import (
    initial_state_8,
    autonomous_validation_agent,
    validation_router,
    autonomous_router
)

from agents import (
    fault_injection_agent,
    route_after_execution
)

from workflow import build_workflow

from parallel_workflow import build_parallel_workflow

from parallel_branch_workflow import (
    build_parallel_branch_workflow
)

from parallel_executor import parallel_executor_agent


def test_initial_state():

    state = copy.deepcopy(initial_state_8)

    assert state["retry_count"] == 0
    assert state["max_retries"] == 3
    assert state["results"] == []
    assert state["retry_history"] == []


def test_successful_execution_routing():

    state = {
        "results": [
            {
                "path": "/posts/1",
                "expected": 200,
                "actual": 200,
                "error": None
            }
        ]
    }

    assert route_after_execution(state) == "reporter"


def test_failed_execution_routing():

    state = {
        "results": [
            {
                "path": "/posts/1",
                "expected": 404,
                "actual": 200,
                "error": None
            }
        ]
    }

    assert route_after_execution(state) == "bug_analyzer"


def test_fault_injection():

    state = copy.deepcopy(initial_state_8)

    state["test_cases"] = [
        {
            "path": "/posts/1",
            "expected_status": 200
        }
    ]

    result = asyncio.run(
        fault_injection_agent(state)
    )

    injected = [
        test
        for test in result["test_cases"]
        if test["path"] == "/posts/1"
    ]

    assert len(injected) == 1
    assert injected[0]["expected_status"] == 404


def create_failed_state(proposed_status):

    state = copy.deepcopy(initial_state_8)

    state["results"] = [
        {
            "path": "/posts/1",
            "expected": 404,
            "actual": 200,
            "error": None
        }
    ]

    state["correction_proposals"] = [
        {
            "path": "/posts/1",
            "proposed_expected_status": proposed_status,
            "reason": "Regression test"
        }
    ]

    return state


def test_valid_correction():

    state = create_failed_state(200)

    result = asyncio.run(
        autonomous_validation_agent(state)
    )

    corrections = result["validated_corrections"]

    assert len(corrections) == 1
    assert corrections[0]["expected_status"] == 200


@pytest.mark.parametrize(
    "status",
    [404, 500, 201]
)
def test_invalid_correction(status):

    state = create_failed_state(status)

    result = asyncio.run(
        autonomous_validation_agent(state)
    )

    assert result["validated_corrections"] == []


def test_retry_limit_routing():

    state = copy.deepcopy(initial_state_8)

    state["retry_count"] = state["max_retries"]

    assert autonomous_router(state) == "reporter"


def test_no_valid_corrections_routing():

    state = copy.deepcopy(initial_state_8)

    state["validated_corrections"] = []

    assert validation_router(state) == "reporter"


@pytest.mark.parametrize(
    "builder",
    [
        build_workflow,
        build_parallel_workflow,
        build_parallel_branch_workflow
    ]
)
def test_workflow_compilation(builder):

    workflow = builder()

    assert workflow is not None
    assert callable(workflow.ainvoke)


@pytest.mark.parametrize(
    "concurrency",
    [0, -1, 1.5, True]
)
def test_invalid_concurrency(concurrency):

    with pytest.raises(ValueError):

        asyncio.run(
            parallel_executor_agent(
                {"test_cases": []},
                max_concurrency=concurrency
            )
        )
