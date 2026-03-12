"""
Workflow Scheduler -- APScheduler-based periodic workflow execution.

Uses APScheduler's AsyncIOScheduler to schedule and manage recurring
workflow runs. Each scheduled job triggers the LangGraph pipeline
in the background.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from backend.database.db import get_db
from backend.orchestration.workflow_graph import workflow_app
from backend.utils.logger import get_logger

logger = get_logger("scheduler")

# ── Singleton scheduler instance ─────────────────────────────

_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the singleton scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
    return _scheduler


def start_scheduler():
    """Start the scheduler if not already running."""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started.")


def shutdown_scheduler():
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down.")
    _scheduler = None


# ── Scheduled job callback ───────────────────────────────────

async def _execute_scheduled_workflow(
    workflow_type: str,
    file_path: str,
    expected_columns: list[str] | None = None,
    email_recipients: list[str] | None = None,
    slack_channel: str | None = None,
):
    """Callback executed by APScheduler to trigger a workflow run."""
    logger.info(f"Scheduled workflow triggered: type={workflow_type}")
    db = get_db()

    try:
        # 1. Create a new workflow_run record in the database
        run_record = await db.create_workflow_run(
            workflow_type=workflow_type,
            input_config={
                "file_path": file_path,
                "trigger": "scheduled",
                "triggered_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        run_id = run_record["id"]
        logger.info(f"Scheduled workflow run created: {run_id}")

        # 2. Update status to running
        await db.update_workflow_run(run_id, {"status": "running"})

        # 3. Build initial state
        initial_state = {
            "run_id": run_id,
            "workflow_type": workflow_type,
            "file_path": file_path,
            "expected_columns": expected_columns or [],
            "email_recipients": email_recipients or [],
            "slack_channel": slack_channel,
            "status": "pending",
            "needs_approval": False,
        }
        config = {"configurable": {"thread_id": run_id}}

        # 4. Execute the graph
        async for event in workflow_app.astream(initial_state, config=config):
            for node_name, state_update in event.items():
                logger.info(f"Scheduled [{run_id}] finished node: {node_name}")
                if state_update.get("status") == "failed":
                    await db.update_workflow_run(
                        run_id,
                        {"status": "failed", "error_message": state_update.get("error", "Unknown")},
                    )
                    return

        # 5. Mark final status
        final_state = workflow_app.get_state(config)
        status = final_state.values.get("status", "completed")
        await db.update_workflow_run(run_id, {"status": status})
        logger.info(f"Scheduled workflow [{run_id}] finished with status: {status}")

    except Exception as e:
        logger.error(f"Scheduled workflow execution failed: {e}")


# ── Public API for adding/removing schedules ─────────────────

def add_interval_schedule(
    job_id: str,
    workflow_type: str,
    file_path: str,
    hours: int = 24,
    minutes: int = 0,
    expected_columns: list[str] | None = None,
    email_recipients: list[str] | None = None,
    slack_channel: str | None = None,
) -> Dict[str, Any]:
    """Add an interval-based recurring schedule (e.g., every 24 hours)."""
    scheduler = get_scheduler()

    trigger = IntervalTrigger(hours=hours, minutes=minutes)
    scheduler.add_job(
        _execute_scheduled_workflow,
        trigger=trigger,
        id=job_id,
        replace_existing=True,
        kwargs={
            "workflow_type": workflow_type,
            "file_path": file_path,
            "expected_columns": expected_columns,
            "email_recipients": email_recipients,
            "slack_channel": slack_channel,
        },
    )
    logger.info(f"Added interval schedule: {job_id} (every {hours}h {minutes}m)")
    return {"job_id": job_id, "type": "interval", "hours": hours, "minutes": minutes}


def add_cron_schedule(
    job_id: str,
    workflow_type: str,
    file_path: str,
    cron_expression: str,
    expected_columns: list[str] | None = None,
    email_recipients: list[str] | None = None,
    slack_channel: str | None = None,
) -> Dict[str, Any]:
    """
    Add a cron-based schedule.

    Example cron_expression: "0 8 * * MON-FRI"  (8 AM weekdays)
    APScheduler CronTrigger accepts: minute, hour, day, month, day_of_week
    """
    scheduler = get_scheduler()

    # Parse cron expression: "min hour day month day_of_week"
    parts = cron_expression.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: '{cron_expression}'. Expected 5 fields.")

    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
    )

    scheduler.add_job(
        _execute_scheduled_workflow,
        trigger=trigger,
        id=job_id,
        replace_existing=True,
        kwargs={
            "workflow_type": workflow_type,
            "file_path": file_path,
            "expected_columns": expected_columns,
            "email_recipients": email_recipients,
            "slack_channel": slack_channel,
        },
    )
    logger.info(f"Added cron schedule: {job_id} ({cron_expression})")
    return {"job_id": job_id, "type": "cron", "cron_expression": cron_expression}


def remove_schedule(job_id: str) -> bool:
    """Remove a scheduled job by ID."""
    scheduler = get_scheduler()
    job = scheduler.get_job(job_id)
    if job:
        scheduler.remove_job(job_id)
        logger.info(f"Removed schedule: {job_id}")
        return True
    return False


def list_schedules() -> list[Dict[str, Any]]:
    """List all currently active schedules."""
    scheduler = get_scheduler()
    jobs = scheduler.get_jobs()

    result = []
    for job in jobs:
        next_run = job.next_run_time.isoformat() if job.next_run_time else None
        result.append({
            "job_id": job.id,
            "next_run": next_run,
            "trigger": str(job.trigger),
            "kwargs": job.kwargs,
        })

    return result
