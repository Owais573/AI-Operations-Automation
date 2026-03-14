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

@router.post("/{report_id}/share/slack", response_model=Dict[str, Any])
async def share_report_slack(report_id: str):
    """Manually share a report to Slack."""
    db = get_db()
    report = await db.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    try:
        # We can reuse the DeliveryAgent's slack logic without logging it as a formal workflow run
        from backend.agents.delivery_agent import DeliveryAgent
        agent = DeliveryAgent(db=db)
        title = report.get("title", f"Report {report_id}")
        markdown = report.get("content_markdown", "")
        
        # Include PDF link in message if available
        pdf_url = report.get("pdf_public_url")
        if pdf_url:
            markdown += f"\n\n**📄 [Download PDF Report]({pdf_url})**"
            
        result = await agent._send_slack(title, {}, markdown)
        
        if result.get("status") == "failed":
            raise HTTPException(status_code=500, detail=result.get("detail", "Slack delivery failed"))
            
        return {"status": "success", "message": "Report shared to Slack"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Note: Download PDF would go here once Supabase Storage or local static files are fully enabled.
