from fastapi import APIRouter, BackgroundTasks, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import shutil
from uuid import uuid4

from backend.database.db import get_db
from backend.orchestration.workflow_graph import workflow_app
from backend.utils.logger import get_logger

logger = get_logger("api.workflows")
router = APIRouter(prefix="/api/workflows", tags=["Workflows"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class WorkflowRunRequest(BaseModel):
    workflow_type: str
    file_path: Optional[str] = None
    expected_columns: Optional[List[str]] = None
    email_recipients: Optional[List[str]] = None
    slack_channel: Optional[str] = None


async def run_workflow_background(run_id: str, workflow_type: str, file_path: str):
    """Background task to execute the workflow graph up to the approval gate."""
    logger.info(f"Starting background workflow execution: {run_id}")
    db = get_db()
    
    try:
        # Update DB status
        await db.update_workflow_run(run_id, {"status": "running"})
        
        initial_state = {
            "run_id": run_id,
            "workflow_type": workflow_type,
            "file_path": file_path,
            "expected_columns": [], # Default for auto-discovery
            "email_recipients": [], 
            "slack_channel": None,
            "status": "pending",
            "needs_approval": False
        }

        config = {"configurable": {"thread_id": run_id}}
        
        # Execute the graph stream
        async for event in workflow_app.astream(initial_state, config=config):
            for node_name, state_update in event.items():
                logger.info(f"Workflow [{run_id}] finished node: {node_name}")
                if "error" in state_update and state_update["status"] == "failed":
                    await db.update_workflow_run(
                        run_id, 
                        {"status": "failed", "error_message": state_update["error"]}
                    )
                    return

        # Check final state after pausing
        final_state = workflow_app.get_state(config)
        status = final_state.values.get("status", "completed")
        
        await db.update_workflow_run(run_id, {"status": status})
        logger.info(f"Workflow [{run_id}] paused/finished with status: {status}")
        
    except Exception as e:
        logger.error(f"Fatal error in background workflow {run_id}: {e}")
        await db.update_workflow_run(run_id, {"status": "failed", "error_message": str(e)})


@router.post("/run", response_model=Dict[str, Any])
async def trigger_workflow(
    background_tasks: BackgroundTasks,
    workflow_type: str = Form(...),
    file: UploadFile = File(...)
):
    """Trigger a new workflow run with an uploaded file."""
    db = get_db()
    try:
        # Save file
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Create run record
        run_record = await db.create_workflow_run(
            workflow_type=workflow_type,
            input_config={"file_name": file.filename, "file_path": file_path}
        )
        run_id = run_record["id"]
        
        # Add background task
        background_tasks.add_task(run_workflow_background, run_id, workflow_type, file_path)
        
        return {
            "message": "Workflow started successfully",
            "run_id": run_id,
            "status": "running",
            "file_name": file.filename
        }
    except Exception as e:
        logger.error(f"Error starting workflow: {e}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs", response_model=List[Dict[str, Any]])
async def list_workflow_runs(limit: int = 50, offset: int = 0):
    """List recent workflow runs."""
    db = get_db()
    runs = await db.list_workflow_runs(limit=limit, offset=offset)
    return runs


@router.get("/runs/{run_id}", response_model=Dict[str, Any])
async def get_workflow_run(run_id: str):
    """Get details of a specific workflow run including agent logs."""
    db = get_db()
    run = await db.get_workflow_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    logs = await db.get_agent_logs_for_run(run_id)
    
    return {
        "run": run,
        "logs": logs
    }


@router.delete("/runs/{run_id}", response_model=Dict[str, Any])
async def delete_workflow_run(run_id: str):
    """Delete a workflow run and all its associated data."""
    db = get_db()
    
    # Check if exists first
    run = await db.get_workflow_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    success = await db.delete_workflow_run(run_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete run")
        
    return {"message": "Workflow run and all associated data deleted successfully"}
