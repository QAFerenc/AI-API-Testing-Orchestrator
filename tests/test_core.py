import asyncio
import json
import pytest

from api_mcp_server import test_api as execute_api_test
from error_logging import classify_exception
from error_logging import classify_api_result
from performance_metrics import calculate_statistics
from json_reporter import test_passed as result_passed
from config import MAX_RETRIES
from parallel_executor import MAX_CONCURRENT_REQUESTS


def test_default_retry_limit():
    assert MAX_RETRIES == 3


def test_default_concurrency_limit():
    assert MAX_CONCURRENT_REQUESTS == 5


@pytest.mark.parametrize(
    "error, expected",
    [
        (TimeoutError(), "TIMEOUT"),
        (ConnectionError(), "CONNECTION_ERROR"),
        (ValueError(), "VALIDATION_ERROR"),
        (AssertionError(), "ASSERTION_ERROR"),
        (RuntimeError(), "UNEXPECTED_ERROR")
    ]
)
def test_exception_classification(error, expected):
    assert classify_exception(error) == expected


@pytest.mark.parametrize(
    "path",
    [
        "/invalid/1",
        "/posts/abc",
        "/users/-1",
        "https://example.com",
        "/posts/1?query=value"
    ]
)
def test_invalid_api_paths(path):

    result = json.loads(
        asyncio.run(execute_api_test(path))
    )

    assert result["status_code"] is None
    assert result["error"] == "Invalid or unsupported API path"


def test_resource_id_length():

    result = json.loads(
        asyncio.run(execute_api_test("/posts/1234567890"))
    )

    assert result["status_code"] is None
    assert result["error"] == "Resource ID too long"


def test_successful_assertion():

    result = {
        "expected": 200,
        "actual": 200,
        "error": None
    }

    assert result_passed(result)


def test_failed_assertion():

    result = {
        "expected": 404,
        "actual": 200,
        "error": None
    }

    assert not result_passed(result)

    assert classify_api_result(result) == "ASSERTION_FAILURE"


def test_api_error_result():

    result = {
        "expected": 200,
        "actual": None,
        "error": "Connection failed"
    }

    assert not result_passed(result)

    assert classify_api_result(result) == "API_EXECUTION_ERROR"


def test_performance_statistics():

    statistics = calculate_statistics(
        [1.0, 2.0, 3.0, 4.0, 5.0]
    )

    assert statistics["count"] == 5
    assert statistics["total"] == 15.0
    assert statistics["average"] == 3.0
    assert statistics["minimum"] == 1.0
    assert statistics["maximum"] == 5.0
    assert statistics["median"] == 3.0
    assert statistics["p95"] == 5.0


def test_empty_performance_statistics():

    statistics = calculate_statistics([])

    assert statistics["count"] == 0
    assert statistics["total"] == 0.0
    assert statistics["average"] is None
