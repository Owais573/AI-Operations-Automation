from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from backend.database.db import get_db
from backend.agents.chat_agent import ChatAgent
from backend.agents.embedding_agent import EmbeddingAgent

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("", response_model=List[Dict[str, Any]])
async def list_reports(limit: int = 50, offset: int = 0):
    """List most recently generated reports."""
    db = get_db()
    reports = await db.list_reports(limit=limit, offset=offset)
    return reports


@router.post("/search", response_model=List[Dict[str, Any]])
async def search_reports(payload: Dict[str, Any]):
    """Semantic search for reports using RAG or keyword fallback."""
    db = get_db()
    query = payload.get("query")
    if not query:
        return []
        
    try:
        # Generate embedding for the query
        agent = EmbeddingAgent(db=db)
        embedding = await agent.generate_embedding(query)
        
        # Search via DB (Vector + Keyword fallback)
        results = await db.search_reports(embedding=embedding, query=query)
        return results
    except Exception as e:
        # Fallback to simple keyword search if EmbeddingAgent fails
        return await db.search_reports(query=query)


@router.get("/{report_id}", response_model=Dict[str, Any])
async def get_report(report_id: str):
    """Get a specific report by its ID, including structured aggregation measurements."""
    db = get_db()
    report = await db.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    # Attempt to fetch aggregated measurements and analysis insights
    run_id = report.get("run_id")
    if run_id:
        logs = await db.get_agent_logs_for_run(run_id)
        
        # 1. Measurements from aggregation_agent
        agg_log = next((l for l in logs if l["agent_name"] == "aggregation_agent" and l["status"] == "completed"), None)
        if agg_log and agg_log.get("output_data"):
            report["measurements"] = agg_log["output_data"].get("aggregations", [])
            
        # 2. Insights from analysis_agent
        ana_log = next((l for l in logs if l["agent_name"] == "analysis_agent" and l["status"] == "completed"), None)
        if ana_log and ana_log.get("output_data"):
            report["insights"] = ana_log["output_data"].get("insights", {})
            
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

@router.post("/{report_id}/chat", response_model=Dict[str, Any])
async def chat_with_report(report_id: str, payload: Dict[str, Any]):
    """Chat with the AI about a specific report's data."""
    db = get_db()
    report = await get_report(report_id)  # Reuses get_report to include measurements/insights
    
    query = payload.get("query")
    history = payload.get("history", [])
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
        
    try:
        agent = ChatAgent(db=db)
        answer = await agent.chat(report, query, history)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Note: Download PDF would go here once Supabase Storage or local static files are fully enabled.
