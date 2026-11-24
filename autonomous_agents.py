from typing import TypedDict

from config import MAX_RETRIES

from agents import (
    executor_agent,
    bug_analyzer_agent,
    correction_agent,
    validation_agent
)


# ==========================================
# 1. AUTONOMOUS STATE
# ==========================================

class AutonomousTestState(TypedDict):

    test_cases: list
    results: list
    report: str
    bug_analysis: str
    correction_proposals: list
    validated_corrections: list
    retry_results: list
    retry_count: int
    max_retries: int
    retry_history: list
    stop_reason: str


initial_state_8 = {
    "test_cases": [],
    "results": [],
    "report": "",
    "bug_analysis": "",
    "correction_proposals": [],
    "validated_corrections": [],
    "retry_results": [],
    "retry_count": 0,
    "max_retries": MAX_RETRIES,
    "retry_history": [],
    "stop_reason": ""
}


# ==========================================
# 2. AUTONOMOUS RETRY AGENT
# ==========================================

async def autonomous_retry_agent(state):

    print(
        f"Autonomous Retry Agent: attempt "
        f"{state['retry_count'] + 1}/{state['max_retries']}"
    )

    corrections = state["validated_corrections"]

    if not corrections:
        return {
            "retry_results": [],
            "stop_reason": "No validated corrections available"
        }

    if state["retry_count"] >= state["max_retries"]:
        return {
            "stop_reason": "Maximum retry attempts reached"
        }

    retry_cases = [
        {
            "path": item["path"],
            "expected_status": item["expected_status"]
        }
        for item in corrections
    ]

    retry_output = await executor_agent({
        "test_cases": retry_cases
    })

    retry_results = retry_output["results"]

    attempt_number = state["retry_count"] + 1

    history_entry = {
        "attempt": attempt_number,
        "test_cases": retry_cases,
        "results": retry_results
    }

    return {
        "retry_count": attempt_number,
        "retry_results": retry_results,
        "retry_history": (
            state["retry_history"] + [history_entry]
        )
    }


# ==========================================
# 3. RETRY EVALUATION AGENT
# ==========================================

async def retry_evaluation_agent(state):

    print("Retry Evaluation Agent: evaluating results")

    results = state["retry_results"]

    if not results:
        return {
            "stop_reason": "No retry results available"
        }

    failed = [
        r for r in results
        if r["actual"] != r["expected"]
        or r.get("error")
    ]

    if not failed:

        print("All retried tests passed.")

        return {
            "stop_reason": "All retried tests passed"
        }

    if state["retry_count"] >= state["max_retries"]:

        print("Maximum retry attempts reached.")

        return {
            "stop_reason": "Maximum retry attempts reached"
        }

    print("Failures remain. Another analysis is required.")

    return {"stop_reason": ""}


# ==========================================
# 4. AUTONOMOUS ROUTER
# ==========================================

def autonomous_router(state):

    print("Autonomous Router: checking next action")

    if state.get("stop_reason"):

        print("Stopping:", state["stop_reason"])

        return "reporter"

    if state["retry_count"] >= state["max_retries"]:

        print("Stopping: retry limit reached")

        return "reporter"

    failed = [
        r for r in state["retry_results"]
        if r["actual"] != r["expected"]
        or r.get("error")
    ]

    if not failed:
        return "reporter"

    print("Continuing autonomous investigation")

    return "bug_analyzer"


# ==========================================
# 5. AUTONOMOUS BUG ANALYZER
# ==========================================

async def autonomous_bug_analyzer(state):

    latest_results = (
        state["retry_results"]
        if state["retry_count"] > 0
        else state["results"]
    )

    return await bug_analyzer_agent({
        **state,
        "results": latest_results
    })


# ==========================================
# 6. AUTONOMOUS CORRECTION AGENT
# ==========================================

async def autonomous_correction_agent(state):

    latest_results = (
        state["retry_results"]
        if state["retry_count"] > 0
        else state["results"]
    )

    return await correction_agent({
        **state,
        "results": latest_results
    })


# ==========================================
# 7. AUTONOMOUS VALIDATION AGENT
# ==========================================

async def autonomous_validation_agent(state):

    latest_results = (
        state["retry_results"]
        if state["retry_count"] > 0
        else state["results"]
    )

    output = await validation_agent({
        **state,
        "results": latest_results
    })

    if not output["validated_corrections"]:

        output["stop_reason"] = (
            "No validated corrections available"
        )

    elif state["retry_count"] >= state["max_retries"]:

        output["stop_reason"] = (
            "Maximum retry attempts reached"
        )

    else:

        output["stop_reason"] = ""

    return output


# ==========================================
# 8. VALIDATION ROUTER
# ==========================================

def validation_router(state):

    print("Validation Router: checking corrections")

    if not state["validated_corrections"]:

        print("No validated corrections. Stopping.")

        return "reporter"

    if state["retry_count"] >= state["max_retries"]:

        print("Retry limit reached. Stopping.")

        return "reporter"

    print("Validated corrections found.")

    return "retry"


# ==========================================
# 9. AUTONOMOUS REPORTER
# ==========================================

async def autonomous_reporter_agent(state):

    print("Autonomous Reporter: generating final report")

    lines = [
        "AUTONOMOUS AI API TEST REPORT",
        "=" * 55
    ]

    lines.append("\nORIGINAL TEST RESULTS")

    latest = {
        r["path"]: r
        for r in state["results"]
    }

    for result in state["results"]:

        passed = (
            result["actual"] == result["expected"]
            and not result.get("error")
        )

        lines.append(
            f"{result['path']}: "
            f"{'PASS' if passed else 'FAIL'} | "
            f"Expected: {result['expected']} | "
            f"Actual: {result['actual']}"
        )

    lines.append("\nAUTONOMOUS RETRY HISTORY")

    if not state["retry_history"]:
        lines.append("No retries performed.")

    for attempt in state["retry_history"]:

        lines.append(
            f"\nRetry attempt {attempt['attempt']}"
        )

        for result in attempt["results"]:

            latest[result["path"]] = result

            passed = (
                result["actual"] == result["expected"]
                and not result.get("error")
            )

            lines.append(
                f"{result['path']}: "
                f"{'PASS' if passed else 'FAIL'} | "
                f"Expected: {result['expected']} | "
                f"Actual: {result['actual']}"
            )

    unresolved = [
        r for r in latest.values()
        if r["actual"] != r["expected"]
        or r.get("error")
    ]

    stop_reason = state.get("stop_reason")

    if not stop_reason:

        if not unresolved:
            stop_reason = "All original tests passed"

        elif state["retry_count"] >= state["max_retries"]:
            stop_reason = "Maximum retry attempts reached"

        else:
            stop_reason = "Workflow completed"

    lines.append("\nEXECUTION SUMMARY")

    lines.append(
        f"Retry attempts: {state['retry_count']}"
    )

    lines.append(
        f"Maximum retries: {state['max_retries']}"
    )

    lines.append(
        f"Stop reason: {stop_reason}"
    )

    lines.append(
        f"Unresolved failures: {len(unresolved)}"
    )

    if unresolved:

        lines.append("\nUNRESOLVED TESTS")

        for result in unresolved:
            lines.append(str(result))

    lines.append("\nLATEST AI BUG ANALYSIS")

    lines.append(
        state.get("bug_analysis") or "No analysis required."
    )

    return {
        "report": "\n".join(lines),
        "stop_reason": stop_reason
    }
