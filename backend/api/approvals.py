from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
from pydantic import BaseModel

from backend.database.db import get_db
from backend.orchestration.workflow_graph import workflow_app
from backend.utils.logger import get_logger

logger = get_logger("api.approvals")
router = APIRouter(prefix="/api/approvals", tags=["Approvals"])


class ApprovalDecision(BaseModel):
    reviewer_notes: str = ""


async def resume_workflow_background(run_id: str):
    """Resume the LangGraph workflow after human approval."""
    logger.info(f"Resuming workflow {run_id} after approval.")
    db = get_db()
    
    try:
        config = {"configurable": {"thread_id": run_id}}
        
        # Update the graph state to release the conditional hold
        workflow_app.update_state(config, {"needs_approval": False, "status": "running"})
        await db.update_workflow_run(run_id, {"status": "running"})
        
        # Stream the remaining nodes (report generation & delivery)
        async for event in workflow_app.astream(None, config=config):
            for node_name, state_update in event.items():
                logger.info(f"Workflow [{run_id}] finished node: {node_name}")
                if "error" in state_update and state_update["status"] == "failed":
                    await db.update_workflow_run(
                        run_id, 
                        {"status": "failed", "error_message": state_update["error"]}
                    )
                    return
        
        # Final pass marks the graph completed
        final_state = workflow_app.get_state(config)
        status = final_state.values.get("status", "completed")
        await db.update_workflow_run(run_id, {"status": status})
        logger.info(f"Workflow [{run_id}] completely finished with status: {status}")
        
    except Exception as e:
        logger.error(f"Fatal error resuming workflow {run_id}: {e}")
        await db.update_workflow_run(run_id, {"status": "failed", "error_message": str(e)})


@router.get("/pending", response_model=List[Dict[str, Any]])
async def list_pending_approvals():
    """List all workflow runs awaiting human approval."""
    db = get_db()
    return await db.get_pending_approvals()


@router.get("/{approval_id}", response_model=Dict[str, Any])
async def get_approval(approval_id: str):
    """Get approval details including data snapshot for review."""
    db = get_db()
    approval = await db.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/{approval_id}/approve", response_model=Dict[str, Any])
async def approve_workflow(
    approval_id: str, 
    decision: ApprovalDecision, 
    background_tasks: BackgroundTasks
):
    """Approve the run and resume the workflow graph."""
    db = get_db()
    
    # 1. Update DB approval record
    approval = await db.get_approval(approval_id)
    if not approval or approval["status"] != "pending":
        raise HTTPException(status_code=400, detail="Approval not found or already decided")
        
    await db.update_approval(approval_id, "approved", decision.reviewer_notes)
    
    # 2. Trigger background task to resume the LangGraph workflow
    run_id = approval["run_id"]
    background_tasks.add_task(resume_workflow_background, run_id)
    
    return {
        "message": f"Approval {approval_id} processed. Workflow resuming.",
        "status": "approved",
        "run_id": run_id
    }


@router.post("/{approval_id}/reject", response_model=Dict[str, Any])
async def reject_workflow(approval_id: str, decision: ApprovalDecision):
    """Reject the workflow run and halt the pipeline completely."""
    db = get_db()
    
    approval = await db.get_approval(approval_id)
    if not approval or approval["status"] != "pending":
        raise HTTPException(status_code=400, detail="Approval not found or already decided")
        
    await db.update_approval(approval_id, "rejected", decision.reviewer_notes)
    
    # Explicitly fail the workflow run
    run_id = approval["run_id"]
    await db.update_workflow_run(
        run_id, 
        {"status": "failed", "error_message": f"Rejected by human: {decision.reviewer_notes}"}
    )
    
    # Update LangGraph state to flag the termination
    config = {"configurable": {"thread_id": run_id}}
    workflow_app.update_state(config, {"needs_approval": False, "status": "failed"})
    
    return {
        "message": "Workflow run rejected and terminated.",
        "status": "rejected",
        "run_id": run_id
    }
