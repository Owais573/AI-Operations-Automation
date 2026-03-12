from fastapi import APIRouter
from typing import Dict, Any

from backend.database.db import get_db

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=Dict[str, Any])
async def get_dashboard_stats():
    """Retrieve high-level statistics for the dashboard UI."""
    db = get_db()
    
    # Simple aggregates (in a real app, optimize via raw SQL count queries)
    runs = await db.list_workflow_runs(limit=1000)
    reports = await db.list_reports(limit=1000)
    pending_approvals = await db.get_pending_approvals()
    
    total_runs = len(runs)
    successful_runs = len([r for r in runs if r.get("status") == "completed"])
    failed_runs = len([r for r in runs if r.get("status") == "failed"])
    
    success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
    
    return {
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "success_rate_percentage": round(success_rate, 2),
        "total_reports_generated": len(reports),
        "pending_human_approvals": len(pending_approvals)
    }


@router.get("/activity", response_model=Dict[str, Any])
async def get_recent_activity():
    """Retrieve a chronological activity feed for the dashboard UI."""
    db = get_db()
    runs = await db.list_workflow_runs(limit=10)
    
    return {
        "recent_runs": runs
    }
