import time
import uuid
import logging

from langchain_core.callbacks import AsyncCallbackHandler
from logging_config import log_event


class AgentLoggingCallback(AsyncCallbackHandler):

    MONITORED_NODES = {
        "planner",
        "fault_injection",
        "executor",
        "analysis_dispatch",
        "bug_analyzer",
        "correction",
        "validation",
        "retry",
        "retry_evaluation",
        "reporter"
    }

    def __init__(self, execution_id=None):

        super().__init__()

        self.execution_id = (
            execution_id or str(uuid.uuid4())
        )

        self.active_runs = {}
        self.completed_runs = []

    async def on_chain_start(
        self,
        serialized,
        inputs,
        *,
        run_id,
        parent_run_id=None,
        tags=None,
        metadata=None,
        **kwargs
    ):

        node_name = kwargs.get("name")

        if node_name not in self.MONITORED_NODES:
            return

        if (metadata or {}).get(
            "langgraph_node"
        ) != node_name:
            return

        self.active_runs[run_id] = {
            "agent": node_name,
            "start": time.perf_counter()
        }

        log_event(
            logging.INFO,
            f"Agent started: {node_name}",
            agent=node_name,
            event="agent_started",
            execution_id=self.execution_id,
            run_id=str(run_id)
        )

    async def on_chain_end(
        self,
        outputs,
        *,
        run_id,
        **kwargs
    ):

        if run_id not in self.active_runs:
            return

        record = self.active_runs.pop(run_id)

        duration = (
            time.perf_counter() - record["start"]
        )

        node_name = record["agent"]

        self.completed_runs.append({
            "agent": node_name,
            "run_id": str(run_id),
            "duration_seconds": duration,
            "status": "COMPLETED"
        })

        log_event(
            logging.INFO,
            f"Agent completed: {node_name}",
            agent=node_name,
            event="agent_completed",
            execution_id=self.execution_id,
            run_id=str(run_id),
            duration_seconds=duration
        )

    async def on_chain_error(
        self,
        error,
        *,
        run_id,
        **kwargs
    ):

        if run_id not in self.active_runs:
            return

        record = self.active_runs.pop(run_id)

        duration = (
            time.perf_counter() - record["start"]
        )

        node_name = record["agent"]

        self.completed_runs.append({
            "agent": node_name,
            "run_id": str(run_id),
            "duration_seconds": duration,
            "status": "ERROR"
        })

        log_event(
            logging.ERROR,
            f"Agent failed: {node_name}",
            agent=node_name,
            event="agent_failed",
            execution_id=self.execution_id,
            run_id=str(run_id),
            duration_seconds=duration,
            error_type=type(error).__name__
        )
