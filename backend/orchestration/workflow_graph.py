from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.orchestration.state import WorkflowState
from backend.orchestration.nodes import (
    ingest_node,
    clean_node,
    aggregate_node,
    analyze_node,
    report_node,
    deliver_node,
)
from backend.utils.logger import get_logger

logger = get_logger("workflow_graph")

# Define conditional edge logic
def should_generate_report(state: WorkflowState) -> str:
    """Check if the workflow is approved to generate the report."""
    # If the workflow failed at any point or is explicitly halted
    if state.get("status") == "failed":
        return END

    # If it needs approval, pause the graph by transitioning to END.
    # Note: When a human approves it, they will update the state
    # to set needs_approval=False, and re-invoke the graph from the
    # current checkpoint, which will then route to generate_report.
    if state.get("needs_approval", False):
        logger.info(f"Workflow {state['run_id']} paused for human approval.")
        return END

    return "generate_report"


def build_workflow() -> StateGraph:
    """Build and compile the LangGraph state machine."""
    workflow = StateGraph(WorkflowState)

    # Add Nodes
    workflow.add_node("ingest", ingest_node)
    workflow.add_node("clean", clean_node)
    workflow.add_node("aggregate", aggregate_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("generate_report", report_node)
    workflow.add_node("deliver", deliver_node)

    # Define simple sequential edges for the first half
    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "clean")
    workflow.add_edge("clean", "aggregate")
    workflow.add_edge("aggregate", "analyze")

    # Define conditional routing after analysis
    workflow.add_conditional_edges(
        "analyze",
        should_generate_report,
        {
            "generate_report": "generate_report",
            END: END
        }
    )

    # Define edges for the final steps
    workflow.add_edge("generate_report", "deliver")
    workflow.add_edge("deliver", END)

    # Compile the graph with an in-memory checkpointer to support pausing for approval
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    
    return app

# Expose the compiled workflow app directly
workflow_app = build_workflow()
