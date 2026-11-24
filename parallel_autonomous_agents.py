from parallel_executor import parallel_executor_agent


async def parallel_autonomous_retry_agent(state):

    print(
        f"Parallel Autonomous Retry Agent: "
        f"attempt {state['retry_count'] + 1}/"
        f"{state['max_retries']}"
    )

    corrections = state["validated_corrections"]

    if not corrections:

        return {
            "retry_results": [],
            "stop_reason":
                "No validated corrections available"
        }

    if state["retry_count"] >= state["max_retries"]:

        return {
            "stop_reason":
                "Maximum retry attempts reached"
        }

    retry_cases = [
        {
            "path": item["path"],
            "expected_status": item["expected_status"]
        }
        for item in corrections
    ]

    retry_output = await parallel_executor_agent(
        {"test_cases": retry_cases}
    )

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

        "retry_history":
            state["retry_history"] + [history_entry]
    }
