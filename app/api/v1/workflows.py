from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.workflows.executor import execute_workflow_async, get_run_status, list_runs
from app.workflows.registry import list_workflows

router = APIRouter(prefix="/workflows", tags=["workflows"])


class TriggerRequest(BaseModel):
    workflow_name: str


class TriggerResponse(BaseModel):
    run_id: str
    workflow_name: str
    status: str


@router.get("/")
async def get_workflows() -> list[str]:
    return list_workflows()


@router.post("/trigger", status_code=202)
async def trigger_workflow(body: TriggerRequest) -> TriggerResponse:
    available = list_workflows()
    if body.workflow_name not in available:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {body.workflow_name!r} not found. Available: {available}",
        )
    run_id = await execute_workflow_async(body.workflow_name)
    return TriggerResponse(run_id=run_id, workflow_name=body.workflow_name, status="running")


@router.get("/status/{run_id}")
async def workflow_status(run_id: str) -> dict:
    run = get_run_status(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found")
    return run


@router.get("/runs")
async def get_runs() -> list[dict]:
    return list_runs()
