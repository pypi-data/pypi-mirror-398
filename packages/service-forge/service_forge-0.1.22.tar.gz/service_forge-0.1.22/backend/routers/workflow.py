from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from models.workflow_model import workflows, WorkflowModel, load_workflow, get_workflow_path
from service_forge.workflow.workflow_factory import create_workflow

router = APIRouter()

@router.get("/", response_model=List[WorkflowModel])
async def get_workflows():
    return workflows

@router.get("/{workflow_id}", response_model=WorkflowModel)
async def get_workflow(workflow_id: str):
    return load_workflow(get_workflow_path(workflow_id))

@router.post("/{workflow_id}")
async def run_workflow(workflow_id: str):
    result = ""

    async def _handle_stream_output(node_name: str, stream):
        nonlocal result
        result += f"[{node_name}] Starting stream output:\n"
        buffer = []
        async for char in stream:
            buffer.append(char)
            result += f"[{node_name}] Received char: '{char}'\n"
        
        complete_message = ''.join(buffer)
        result += f"[{node_name}] Complete message: '{complete_message}'\n"

    workflow = create_workflow(
        config_path=get_workflow_path(workflow_id),
        _handle_stream_output=_handle_stream_output,
    )
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    await workflow.run()

    return {"message": result}
