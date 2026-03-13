"""
Database client for Supabase interactions.
Provides helper methods for common CRUD operations on workflow tables.
"""

from datetime import datetime, timezone
from supabase import create_client, Client
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger("database")


class DatabaseClient:
    """Supabase database client wrapper with helper methods."""

    def __init__(self):
        settings = get_settings()
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
        logger.info("Database client initialized")

    # ─── Workflow Runs ───────────────────────────────────────

    async def create_workflow_run(self, workflow_type: str, input_config: dict | None = None) -> dict:
        """Create a new workflow run record."""
        data = {
            "workflow_type": workflow_type,
            "status": "pending",
            "input_config": input_config or {},
        }
        result = self.client.table("workflow_runs").insert(data).execute()
        logger.info(f"Created workflow run: {result.data[0]['id']}")
        return result.data[0]

    async def update_workflow_run(self, run_id: str, updates: dict) -> dict:
        """Update a workflow run record."""
        result = self.client.table("workflow_runs").update(updates).eq("id", run_id).execute()
        return result.data[0] if result.data else {}

    async def get_workflow_run(self, run_id: str) -> dict | None:
        """Get a single workflow run by ID."""
        result = self.client.table("workflow_runs").select("*").eq("id", run_id).single().execute()
        return result.data

    async def list_workflow_runs(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """List workflow runs ordered by creation date."""
        result = (
            self.client.table("workflow_runs")
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data

    # ─── Agent Logs ──────────────────────────────────────────

    async def create_agent_log(
        self,
        run_id: str,
        agent_name: str,
        status: str = "started",
        input_summary: dict | None = None,
    ) -> dict:
        """Create an agent log entry."""
        data = {
            "run_id": run_id,
            "agent_name": agent_name,
            "status": status,
            "input_summary": input_summary,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        result = self.client.table("agent_logs").insert(data).execute()
        return result.data[0]

    async def update_agent_log(self, log_id: str, updates: dict) -> dict:
        """Update an agent log entry."""
        result = self.client.table("agent_logs").update(updates).eq("id", log_id).execute()
        return result.data[0] if result.data else {}

    async def get_agent_logs_for_run(self, run_id: str) -> list[dict]:
        """Get all agent logs for a workflow run, ordered by creation time."""
        result = (
            self.client.table("agent_logs")
            .select("*")
            .eq("run_id", run_id)
            .order("created_at", desc=False)
            .execute()
        )
        return result.data

    # ─── Reports ─────────────────────────────────────────────

    async def create_report(self, run_id: str, title: str, content_markdown: str, **kwargs) -> dict:
        """Create a report record."""
        # Clean up kwargs to match new schema
        if "content_pdf_url" in kwargs:
            del kwargs["content_pdf_url"]
        if "insights" in kwargs:
            del kwargs["insights"]
            
        data = {
            "run_id": run_id,
            "title": title,
            "content_markdown": content_markdown,
            **kwargs,
        }
        result = self.client.table("reports").insert(data).execute()
        logger.info(f"Created report: {result.data[0]['id']}")
        return result.data[0]

    async def get_report(self, report_id: str) -> dict | None:
        """Get a single report by ID."""
        result = self.client.table("reports").select("*").eq("id", report_id).single().execute()
        return result.data

    async def list_reports(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """List reports ordered by creation date."""
        result = (
            self.client.table("reports")
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data

    # ─── Approvals ───────────────────────────────────────────

    async def create_approval(
        self, run_id: str, checkpoint_name: str, data_snapshot: dict | None = None
    ) -> dict:
        """Create an approval checkpoint record."""
        data = {
            "run_id": run_id,
            "checkpoint_name": checkpoint_name,
            "status": "pending",
            "data_snapshot": data_snapshot,
        }
        result = self.client.table("approvals").insert(data).execute()
        logger.info(f"Created approval checkpoint: {result.data[0]['id']}")
        return result.data[0]

    async def update_approval(self, approval_id: str, status: str, reviewer_notes: str = "") -> dict:
        """Update approval status (approve or reject)."""
        updates = {
            "status": status,
            "reviewer_notes": reviewer_notes,
            "decided_at": datetime.now(timezone.utc).isoformat(),
        }
        result = self.client.table("approvals").update(updates).eq("id", approval_id).execute()
        return result.data[0] if result.data else {}

    async def get_pending_approvals(self) -> list[dict]:
        """Get all pending approvals."""
        result = (
            self.client.table("approvals")
            .select("*, workflow_runs(workflow_type, status)")
            .eq("status", "pending")
            .order("created_at", desc=False)
            .execute()
        )
        return result.data

    async def get_approval(self, approval_id: str) -> dict | None:
        """Get a single approval by ID."""
        result = self.client.table("approvals").select("*").eq("id", approval_id).single().execute()
        return result.data


# Singleton instance
_db_client: DatabaseClient | None = None


def get_db() -> DatabaseClient:
    """Get the singleton database client instance."""
    global _db_client
    if _db_client is None:
        _db_client = DatabaseClient()
    return _db_client
