import logging
import asyncio

from logging_config import log_event
from api_logging import current_execution_id


def classify_exception(error):

    error_type = type(error).__name__

    if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
        return "TIMEOUT"

    if "timeout" in error_type.lower():
        return "TIMEOUT"

    if isinstance(error, ConnectionError):
        return "CONNECTION_ERROR"

    if "connect" in error_type.lower():
        return "CONNECTION_ERROR"

    if isinstance(error, ValueError):
        return "VALIDATION_ERROR"

    if isinstance(error, AssertionError):
        return "ASSERTION_ERROR"

    if error_type in {
        "ServerError",
        "ClientError",
        "APIError"
    }:
        return "AI_PROVIDER_ERROR"

    return "UNEXPECTED_ERROR"


def log_exception(
    error,
    agent,
    event="execution_error",
    level=logging.ERROR,
    **data
):

    category = classify_exception(error)

    execution_id = data.pop(
        "execution_id",
        current_execution_id.get()
    )

    log_event(
        level,
        f"{agent}: {category}",
        agent=agent,
        event=event,
        execution_id=execution_id,
        error_type=type(error).__name__,
        error_category=category,
        **data
    )

    return category


def log_ai_model_failure(agent, model, error):

    return log_exception(
        error,
        agent=agent,
        event="ai_model_failed",
        level=logging.WARNING,
        model=model
    )


def classify_api_result(result):

    error = result.get("error")

    if error:

        if error == "Invalid or unsupported API path":
            return "INVALID_API_PATH"

        if error == "Resource ID too long":
            return "INVALID_RESOURCE_ID"

        return "API_EXECUTION_ERROR"

    if result["actual"] != result["expected"]:
        return "ASSERTION_FAILURE"

    return "NONE"
