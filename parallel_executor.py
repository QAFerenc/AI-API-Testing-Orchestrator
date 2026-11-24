from error_logging import log_exception
from api_logging import start_api_request, finish_api_request
import asyncio
import json
import anyio

from mcp import ClientSession
from api_mcp_server import mcp


MAX_CONCURRENT_REQUESTS = 5


async def execute_single_test(
    session,
    test,
    semaphore
):

    path = test["path"]
    expected = test["expected_status"]

    async with semaphore:

        print("Starting test:", path)
        request_log = start_api_request(path, expected)

        try:

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

            result = {
                "path": path,
                "expected": expected,
                "actual": data.get("status_code"),
                "error": data.get("error")
            }

        except Exception as exc:
            log_exception(
                exc,
                agent="executor",
                event="api_execution_error",
                path=path,
                request_id=request_log["request_id"]
            )

            result = {
                "path": path,
                "expected": expected,
                "actual": None,
                "error": str(exc)
            }

        print(
            "Finished test:",
            path,
            "| Actual:",
            result["actual"]
        )

        finish_api_request(request_log, result)
        return result


async def parallel_executor_agent(
    state,
    max_concurrency=MAX_CONCURRENT_REQUESTS
):

    print("Parallel Executor: running MCP API tests")

    if type(max_concurrency) is not int or max_concurrency < 1:
        raise ValueError("Concurrency must be a positive integer")

    print("Maximum concurrency:", max_concurrency)

    semaphore = asyncio.Semaphore(
        max_concurrency
    )

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

                    tasks = [
                        execute_single_test(
                            session,
                            test,
                            semaphore
                        )
                        for test in state["test_cases"]
                    ]

                    results = await asyncio.gather(
                        *tasks
                    )

            finally:

                tg.cancel_scope.cancel()

    return {"results": results}
