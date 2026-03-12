from typing import Any, Dict, List, Optional, TypedDict


class WorkflowState(TypedDict):
    """
    Represents the state of the LangGraph workflow across agents.
    """
    run_id: str
    workflow_type: str                   # e.g., 'sales_report', 'inventory_report'
    
    # Input
    file_path: Optional[str]
    expected_columns: Optional[List[str]]
    
    # Intermediate data states (kept as lists of dicts or records)
    raw_data: Optional[Dict[str, Any]]        # from IngestionAgent (records, metadata, validation)
    cleaned_data: Optional[Dict[str, Any]]    # from CleaningAgent (records, cleaning_report)
    aggregated_data: Optional[Dict[str, Any]] # from AggregationAgent (aggregated sets)
    analysis: Optional[Dict[str, Any]]        # from AnalysisAgent (insights)
    report: Optional[Dict[str, Any]]          # from ReportGenerationAgent (markdown, pdf_path)
    
    # Delivery info
    email_recipients: Optional[List[str]]
    slack_channel: Optional[str]
    
    # Workflow status
    status: str                          # 'pending', 'running', 'awaiting_approval', 'completed', 'failed'
    error: Optional[str]
    needs_approval: bool
