from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from backend.scheduler.scheduler import (
    add_interval_schedule,
    add_cron_schedule,
    remove_schedule,
    list_schedules,
)
from backend.utils.logger import get_logger

logger = get_logger("api.schedules")
router = APIRouter(prefix="/api/schedules", tags=["Schedules"])


class IntervalScheduleRequest(BaseModel):
    job_id: str
    workflow_type: str
    file_path: str
    hours: int = 24
    minutes: int = 0
    expected_columns: Optional[List[str]] = None
    email_recipients: Optional[List[str]] = None
    slack_channel: Optional[str] = None


class CronScheduleRequest(BaseModel):
    job_id: str
    workflow_type: str
    file_path: str
    cron_expression: str  # e.g., "0 8 * * MON-FRI"
    expected_columns: Optional[List[str]] = None
    email_recipients: Optional[List[str]] = None
    slack_channel: Optional[str] = None


@router.post("/interval", response_model=Dict[str, Any])
async def create_interval_schedule(request: IntervalScheduleRequest):
    """Create a recurring workflow on a fixed interval (e.g. every 24 hours)."""
    try:
        result = add_interval_schedule(
            job_id=request.job_id,
            workflow_type=request.workflow_type,
            file_path=request.file_path,
            hours=request.hours,
            minutes=request.minutes,
            expected_columns=request.expected_columns,
            email_recipients=request.email_recipients,
            slack_channel=request.slack_channel,
        )
        return {"message": "Interval schedule created", **result}
    except Exception as e:
        logger.error(f"Failed to create interval schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cron", response_model=Dict[str, Any])
async def create_cron_schedule(request: CronScheduleRequest):
    """Create a recurring workflow on a cron schedule (e.g. '0 8 * * MON-FRI')."""
    try:
        result = add_cron_schedule(
            job_id=request.job_id,
            workflow_type=request.workflow_type,
            file_path=request.file_path,
            cron_expression=request.cron_expression,
            expected_columns=request.expected_columns,
            email_recipients=request.email_recipients,
            slack_channel=request.slack_channel,
        )
        return {"message": "Cron schedule created", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create cron schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[Dict[str, Any]])
async def get_schedules():
    """List all active schedules."""
    return list_schedules()


@router.delete("/{job_id}", response_model=Dict[str, Any])
async def delete_schedule(job_id: str):
    """Remove a scheduled job by ID."""
    removed = remove_schedule(job_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Schedule '{job_id}' not found")
    return {"message": f"Schedule '{job_id}' removed", "job_id": job_id}
