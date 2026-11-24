from error_logging import log_ai_model_failure
import asyncio
import json
import re
import anyio

from google.genai import types
from mcp import ClientSession

from config import ai_client, AI_MODELS
from api_mcp_server import mcp
from api_specification import (
    api_details,
    REFERENCE_EXPECTATIONS
)


# ==========================================
# 1. AI PLANNER AGENT
# ==========================================

async def planner_agent(state):

    print("AI Planner: generating dynamic OpenAPI tests")

    prompt = f"""
    You are a Senior QA Automation Engineer.

    API specification:
    {json.dumps(api_details, indent=2)}

    Generate exactly five unique GET API test cases.

    Reference facts:
    - Posts with IDs 1-100 exist.
    - Users with IDs 1-10 exist.
    - Higher IDs return HTTP 404.

    Include positive and negative test cases.

    Return only JSON in this format:

    {{
        "test_cases": [
            {{
                "path": "/posts/1",
                "expected_status": 200
            }}
        ]
    }}
    """

    for model in AI_MODELS:

        print("Trying AI Planner:", model)

        try:

            response = await asyncio.wait_for(
                ai_client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0
                    )
                ),
                timeout=25
            )

            data = json.loads(response.text)
            cases = data["test_cases"]

            if not isinstance(cases, list) or len(cases) != 5:
                raise ValueError("Expected exactly five tests")

            paths = set()
            statuses = set()

            for case in cases:

                path = case["path"]
                status = case["expected_status"]

                if not re.fullmatch(
                    r"/(posts|users)/[1-9][0-9]{0,8}", path
                ):
                    raise ValueError("Invalid API path")

                if type(status) is not int or status not in (200, 404):
                    raise ValueError("Invalid expected status")

                if path in paths:
                    raise ValueError("Duplicate test case")

                paths.add(path)
                statuses.add(status)

            if statuses != {200, 404}:
                raise ValueError("Missing positive or negative tests")

            print("AI Planner succeeded:", model)

            return {"test_cases": cases}

        except Exception as e:

            log_ai_model_failure("planner", model, e)
            print(
                "Planner model failed:",
                model,
                type(e).__name__
            )

    print("Using deterministic fallback tests")

    return {
        "test_cases": [
            {"path": "/posts/1", "expected_status": 200},
            {"path": "/posts/999999", "expected_status": 404},
            {"path": "/users/1", "expected_status": 200},
            {"path": "/users/99", "expected_status": 404},
            {"path": "/posts/50", "expected_status": 200}
        ]
    }


# ==========================================
# 2. MCP EXECUTOR AGENT
# ==========================================

async def executor_agent(state):

    print("Executor: running dynamic MCP API tests")

    results = []

    client_write, server_read = (
        anyio.create_memory_object_stream(10)
    )

    server_write, client_read = (
        anyio.create_memory_object_stream(10)
    )

    async with (
        client_write,
        server_read,
        server_write,
        client_read
    ):

        async with anyio.create_task_group() as tg:

            tg.start_soon(
                mcp._mcp_server.run,
                server_read,
                server_write,
                mcp._mcp_server.create_initialization_options()
            )

            try:

                async with ClientSession(
                    client_read,
                    client_write
                ) as session:

                    await session.initialize()

                    tools = await session.list_tools()

                    print(
                        "Available MCP tools:",
                        [t.name for t in tools.tools]
                    )

                    for test in state["test_cases"]:

                        path = test["path"]

                        response = await session.call_tool(
                            "test_api",
                            arguments={"path": path}
                        )

                        if response.isError:
                            raise RuntimeError(
                                str(response.content)
                            )

                        data = json.loads(
                            response.content[0].text
                        )

                        results.append({
                            "path": path,
                            "expected": test["expected_status"],
                            "actual": data.get("status_code"),
                            "error": data.get("error")
                        })

            finally:

                tg.cancel_scope.cancel()

    return {"results": results}


# ==========================================
# 3. FAULT INJECTION AGENT
# ==========================================

async def fault_injection_agent(state):

    print("Fault Injector: creating a controlled test failure")

    cases = [
        case.copy()
        for case in state["test_cases"]
        if case["path"] != "/posts/1"
    ]

    cases.insert(
        0,
        {
            "path": "/posts/1",
            "expected_status": 404
        }
    )

    return {"test_cases": cases}


# ==========================================
# 4. CONDITIONAL ROUTER
# ==========================================

def route_after_execution(state):

    failed = any(
        r["actual"] != r["expected"]
        or r.get("error")
        for r in state["results"]
    )

    if failed:

        print("Router: failures detected -> Bug Analyzer")

        return "bug_analyzer"

    print("Router: all tests passed -> Reporter")

    return "reporter"


# ==========================================
# 5. AI BUG ANALYZER AGENT
# ==========================================

async def bug_analyzer_agent(state):

    print("AI Bug Analyzer: investigating failures")

    failed_tests = [
        r for r in state["results"]
        if r["actual"] != r["expected"]
        or r.get("error")
    ]

    if not failed_tests:
        return {"bug_analysis": ""}

    prompt = f"""
    You are a Senior QA Automation Engineer.

    Analyze these failed REST API tests:

    {json.dumps(failed_tests, indent=2)}

    System under test: JSONPlaceholder REST API.

    Trusted reference facts:
    - /posts/1 exists and returns HTTP 200.
    - /posts/999999 does not exist and returns HTTP 404.
    - /users/1 exists and returns HTTP 200.

    For each failure:
    1. Describe the observed failure.
    2. Identify the most likely root cause.
    3. Distinguish incorrect test expectations from API defects.
    4. Suggest a safe next action.

    Do not assume every failed test is an API bug.
    Do not automatically change expected status codes.
    """

    for model in AI_MODELS:

        print("Trying Bug Analyzer:", model)

        try:

            response = await asyncio.wait_for(
                ai_client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0
                    )
                ),
                timeout=25
            )

            if not response.text:
                raise ValueError("Empty AI response")

            print("AI Bug Analyzer succeeded:", model)

            return {
                "bug_analysis": response.text
            }

        except Exception as e:

            log_ai_model_failure("bug_analyzer", model, e)
            print(
                "Bug Analyzer model failed:",
                model,
                type(e).__name__
            )

    return {
        "bug_analysis":
            "AI analysis unavailable. Review the failed "
            "assertion against trusted reference data."
    }


# ==========================================
# 6. AI CORRECTION AGENT
# ==========================================

async def correction_agent(state):

    print("AI Correction Agent: investigating failed tests")

    failed_tests = [
        r for r in state["results"]
        if r["actual"] != r["expected"]
        or r.get("error")
    ]

    if not failed_tests:
        return {"correction_proposals": []}

    prompt = f"""
    You are a Senior QA Automation Engineer.

    Failed API tests:
    {json.dumps(failed_tests, indent=2)}

    Trusted reference facts:
    - /posts/1 exists and returns HTTP 200.
    - /posts/999999 does not exist and returns HTTP 404.
    - /users/1 exists and returns HTTP 200.

    Propose a correction ONLY when the existing expected
    status contradicts trusted reference data.

    Never change an expectation simply because a test failed.

    Return ONLY a JSON array:

    [
        {{
            "path": "/posts/1",
            "proposed_expected_status": 200,
            "reason": "The resource exists according to reference data."
        }}
    ]

    If no justified correction exists, return [].
    """

    for model in AI_MODELS:

        print("Trying Correction Agent:", model)

        try:

            response = await asyncio.wait_for(
                ai_client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0
                    )
                ),
                timeout=25
            )

            proposals = json.loads(response.text)

            if not isinstance(proposals, list):
                raise ValueError("Expected JSON list")

            print("AI Correction Agent succeeded:", model)

            return {
                "correction_proposals": proposals
            }

        except Exception as e:

            log_ai_model_failure("correction", model, e)
            print(
                "Correction model failed:",
                model,
                type(e).__name__
            )

    print("AI correction unavailable")

    return {"correction_proposals": []}


# ==========================================
# 7. VALIDATION AGENT
# ==========================================

async def validation_agent(state):

    print("Validation Agent: checking AI corrections")

    validated = []
    validated_paths = set()

    failed_results = {
        r["path"]: r
        for r in state["results"]
        if r["actual"] != r["expected"]
        or r.get("error")
    }

    for proposal in state["correction_proposals"]:

        if not isinstance(proposal, dict):
            continue

        path = proposal.get("path")
        status = proposal.get("proposed_expected_status")

        if not isinstance(path, str):
            continue

        if path not in failed_results:
            continue

        if path not in REFERENCE_EXPECTATIONS:
            continue

        if type(status) is not int:
            continue

        if status != REFERENCE_EXPECTATIONS[path]:
            continue

        if status == failed_results[path]["expected"]:
            continue

        if path in validated_paths:
            continue

        validated.append({
            "path": path,
            "expected_status": status,
            "reason": proposal.get("reason", "")
        })

        validated_paths.add(path)

    print("Validated corrections:", len(validated))

    return {
        "validated_corrections": validated
    }
