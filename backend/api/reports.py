from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from backend.database.db import get_db

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("", response_model=List[Dict[str, Any]])
async def list_reports(limit: int = 50, offset: int = 0):
    """List most recently generated reports."""
    db = get_db()
    reports = await db.list_reports(limit=limit, offset=offset)
    return reports


@router.get("/{report_id}", response_model=Dict[str, Any])
async def get_report(report_id: str):
    """Get a specific report by its ID."""
    db = get_db()
    report = await db.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

# Note: Download PDF would go here once Supabase Storage or local static files are fully enabled.
