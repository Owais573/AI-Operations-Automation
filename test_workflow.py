import asyncio
import uuid
import sys
import os

from backend.orchestration.workflow_graph import workflow_app
from backend.database.db import get_db
from backend.utils.logger import get_logger

logger = get_logger("test_runner")

async def test_run():
    # Setup test state
    db = get_db()
    # Create workflow run in DB
    run_record = await db.create_workflow_run(
        workflow_type="sales_report",
        input_config={"file_path": "data/mock_sales_data.csv"}
    )
    run_id = run_record["id"]
    logger.info(f"Created workflow run in DB: {run_id}")
    
    initial_state = {
        "run_id": run_id,
        "workflow_type": "sales_report",
        "file_path": "data/mock_sales_data.csv",
        "expected_columns": ["Order Date", "Product Name", "Units Sold", "Revenue"],
        "status": "pending",
        "needs_approval": False
    }

    config = {"configurable": {"thread_id": run_id}}
    
    # Run the graph until the human approval breakpoint
    logger.info("Executing pipeline (Ingest -> Clean -> Aggregate -> Analyze)")
    async for event in workflow_app.astream(initial_state, config=config):
        for node_name, state_update in event.items():
            logger.info(f"==> Completed Node: {node_name}")
            if "error" in state_update and state_update["status"] == "failed":
                logger.error(f"Pipeline failed at {node_name}: {state_update['error']}")
                sys.exit(1)

    # Check state after pausing
    final_state = workflow_app.get_state(config)
    logger.info(f"Workflow paused at status: {final_state.values.get('status')} (needs_approval={final_state.values.get('needs_approval')})")
    
    if final_state.values.get("needs_approval"):
        logger.info("--- HUMAN APPROVAL SIMULATION ---")
        # Simulate human approving via API
        from langgraph.graph import StateGraph
        # Update the state to approve the workflow
        workflow_app.update_state(config, {"needs_approval": False, "status": "running"})
        
        logger.info("Resuming pipeline (Report -> Deliver)")
        async for event in workflow_app.astream(None, config=config):
            for node_name, state_update in event.items():
                logger.info(f"==> Completed Node: {node_name}")
                if "error" in state_update and state_update["status"] == "failed":
                    logger.error(f"Pipeline failed at {node_name}: {state_update['error']}")
                    sys.exit(1)
        
    logger.info("Test execution completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_run())
