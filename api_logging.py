import time
import uuid
import logging

from contextvars import ContextVar
from logging_config import log_event


current_execution_id = ContextVar(
    "current_execution_id",
    default=None
)


def start_api_request(path, expected_status):

    request = {
        "request_id": str(uuid.uuid4()),
        "execution_id": current_execution_id.get(),
        "method": "GET",
        "path": path,
        "expected_status": expected_status,
        "start": time.perf_counter()
    }

    log_event(
        logging.INFO,
        f"API request started: {path}",
        agent="executor",
        event="api_request_started",
        execution_id=request["execution_id"],
        request_id=request["request_id"],
        method=request["method"],
        path=path,
        expected_status=expected_status
    )

    return request


def finish_api_request(request, result):

    duration = (
        time.perf_counter() - request["start"]
    )

    passed = (
        result["actual"] == result["expected"]
        and not result.get("error")
    )

    log_event(
        logging.INFO if passed else logging.WARNING,
        f"API test {'PASS' if passed else 'FAIL'}: "
        f"{request['path']}",
        agent="executor",
        event="api_request_completed",
        execution_id=request["execution_id"],
        request_id=request["request_id"],
        method=request["method"],
        path=request["path"],
        expected_status=result["expected"],
        actual_status=result["actual"],
        test_result="PASS" if passed else "FAIL",
        duration_seconds=duration,
        has_error=bool(result.get("error"))
    )

    return duration
