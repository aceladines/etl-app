import asyncio
import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from loguru import logger

from app.workflows.base import WorkflowResult
from app.workflows.registry import get_workflow

_runs: dict[str, dict] = {}


def _execute_sync(workflow_name: str, run_id: str) -> WorkflowResult:
    workflow = get_workflow(workflow_name)
    return workflow.run()


async def execute_workflow_async(workflow_name: str) -> str:
    """Launch a workflow in the thread pool. Returns run_id immediately."""
    run_id = str(uuid.uuid4())
    _runs[run_id] = {
        "run_id": run_id,
        "workflow_name": workflow_name,
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
    }

    async def _run() -> None:
        try:
            result = await asyncio.to_thread(_execute_sync, workflow_name, run_id)
            _runs[run_id]["status"] = result.status
            _runs[run_id]["result"] = asdict(result)
        except Exception as exc:
            logger.error("Run {run_id} failed: {err}", run_id=run_id, err=exc)
            _runs[run_id]["status"] = "failed"
            _runs[run_id]["result"] = {"error": str(exc)}

    asyncio.create_task(_run())
    return run_id


def get_run_status(run_id: str) -> dict | None:
    return _runs.get(run_id)


def list_runs() -> list[dict]:
    return list(_runs.values())
