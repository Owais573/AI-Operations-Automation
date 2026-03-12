from typing import Dict, Any

from backend.database.db import get_db
from backend.agents.ingestion_agent import IngestionAgent
from backend.agents.cleaning_agent import CleaningAgent
from backend.agents.aggregation_agent import AggregationAgent
from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.report_agent import ReportAgent
from backend.agents.delivery_agent import DeliveryAgent
from backend.orchestration.state import WorkflowState
from backend.utils.logger import get_logger

logger = get_logger("workflow_nodes")


async def ingest_node(state: WorkflowState) -> Dict[str, Any]:
    """Node for data ingestion and validation."""
    logger.info(f"Node [ingest] starting for run_id={state['run_id']}")
    try:
        agent = IngestionAgent(db=get_db())
        input_data = {
            "file_path": state.get("file_path"),
            "expected_columns": state.get("expected_columns", [])
        }
        result = await agent.run(input_data)
        return {
            "raw_data": result,
            "status": "running"
        }
    except Exception as e:
        logger.error(f"Error in ingest_node: {e}")
        return {"status": "failed", "error": str(e)}


async def clean_node(state: WorkflowState) -> Dict[str, Any]:
    """Node for LLM-powered data cleaning."""
    logger.info(f"Node [clean] starting for run_id={state['run_id']}")
    try:
        agent = CleaningAgent(db=get_db())
        raw_data = state.get("raw_data", {})
        input_data = {
            "records": raw_data.get("records", []),
            "metadata": raw_data.get("metadata", {})
        }
        result = await agent.run(input_data)
        return {"cleaned_data": result}
    except Exception as e:
        logger.error(f"Error in clean_node: {e}")
        return {"status": "failed", "error": str(e)}


async def aggregate_node(state: WorkflowState) -> Dict[str, Any]:
    """Node for data aggregation."""
    logger.info(f"Node [aggregate] starting for run_id={state['run_id']}")
    try:
        agent = AggregationAgent(db=get_db())
        cleaned_data = state.get("cleaned_data", {})
        input_data = {
            "records": cleaned_data.get("records", []),
            # Group by logic can be matched to workflow_type or default.
            "group_by": ["product", "region"],
            "report_type": state.get("workflow_type", "sales_report"),
            "time_period": "monthly"
        }
        result = await agent.run(input_data)
        return {"aggregated_data": result}
    except Exception as e:
        logger.error(f"Error in aggregate_node: {e}")
        return {"status": "failed", "error": str(e)}


async def analyze_node(state: WorkflowState) -> Dict[str, Any]:
    """Node for LLM insights generation."""
    logger.info(f"Node [analyze] starting for run_id={state['run_id']}")
    try:
        agent = AnalysisAgent(db=get_db())
        agg_data = state.get("aggregated_data", {})
        clean_data = state.get("cleaned_data", {})
        
        input_data = {
            "overall_metrics": agg_data.get("overall_kpis", {}),
            "time_series": agg_data.get("time_series", []),
            "product_summary": agg_data.get("product_summary", []),
            "region_summary": agg_data.get("region_summary", []),
            "top_performers": agg_data.get("top_performers", {}),
            "cleaning_report": clean_data.get("cleaning_report", {})
        }
        result = await agent.run(input_data)
        
        # After analysis, the workflow pauses for human approval.
        # We record the pending approval checkpoint in the DB.
        db = get_db()
        await db.create_approval(
            run_id=state["run_id"],
            checkpoint_name="pre_report_review",
            data_snapshot=result
        )
        
        return {
            "analysis": result,
            "needs_approval": True,
            "status": "awaiting_approval"
        }
    except Exception as e:
        logger.error(f"Error in analyze_node: {e}")
        return {"status": "failed", "error": str(e)}


# Note: human review is not an active agent node, it's a conditional edge barrier.
# When the human approves via the API, the state 'needs_approval' is set to False,
# and the graph resumes from human_review node's outbound edge.

async def report_node(state: WorkflowState) -> Dict[str, Any]:
    """Node for generating Markdown and PDF reports."""
    logger.info(f"Node [report] starting for run_id={state['run_id']}")
    try:
        agent = ReportAgent(db=get_db())
        analysis = state.get("analysis", {})
        agg_data = state.get("aggregated_data", {})
        workflow_type = state.get("workflow_type", "business_report")
        
        input_data = {
            "report_title": f"Automated {workflow_type.replace('_', ' ').title().strip()}",
            "report_type": workflow_type,
            "insights": analysis,
            "overall_metrics": agg_data.get("overall_kpis", {}),
            "time_series": agg_data.get("time_series", []),
            "product_summary": agg_data.get("product_summary", []),
            "region_summary": agg_data.get("region_summary", []),
            "top_performers": agg_data.get("top_performers", {})
        }
        result = await agent.run(input_data)
        return {"report": result}
    except Exception as e:
        logger.error(f"Error in report_node: {e}")
        return {"status": "failed", "error": str(e)}


async def deliver_node(state: WorkflowState) -> Dict[str, Any]:
    """Node for delivering the report via Slack/Email."""
    logger.info(f"Node [deliver] starting for run_id={state['run_id']}")
    try:
        agent = DeliveryAgent(db=get_db())
        report_data = state.get("report", {})
        analysis_data = state.get("analysis", {})
        workflow_type = state.get("workflow_type", "report")
        
        input_data = {
            "report_markdown": report_data.get("markdown", ""),
            "report_title": f"New Workflow Execution: {workflow_type.replace('_', ' ').title()}",
            "insights": analysis_data,
            "delivery_channels": [], # Populate based on config if needed
            "email_recipients": state.get("email_recipients", []),
            "pdf_path": report_data.get("pdf_path")
        }
        
        # Determine channels based on state configuration
        if state.get("slack_channel"):
            input_data["delivery_channels"].append("slack")
        if state.get("email_recipients"):
            input_data["delivery_channels"].append("email")
            
        result = await agent.run(input_data)
        
        # Workflow finishes
        return {
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Error in deliver_node: {e}")
        return {"status": "failed", "error": str(e)}
