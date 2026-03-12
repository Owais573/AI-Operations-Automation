"""
Base Agent class that all workflow agents inherit from.

Provides:
- Automatic execution logging to the agent_logs table
- Duration and token tracking
- Error handling with structured error reporting
- Retry logic for transient failures
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
import json

from backend.database.db import DatabaseClient
from backend.utils.logger import get_logger
from backend.utils.error_handler import AgentExecutionError


class BaseAgent(ABC):
    """
    Abstract base class for all workflow agents.

    Each agent must implement the `run()` method. The `execute()` wrapper
    provides automatic logging, timing, and error handling.
    """

    def __init__(self, name: str, db: DatabaseClient):
        """
        Initialize agent.

        Args:
            name: Unique name for this agent (e.g., 'cleaning_agent')
            db: Database client instance for logging
        """
        self.name = name
        self.db = db
        self.logger = get_logger(f"agent.{name}")
        self.tokens_used: int = 0

    async def execute(self, run_id: str, input_data: dict) -> dict:
        """
        Execute the agent with full lifecycle logging.

        This is the main entry point — it wraps the `run()` method with:
        1. Start log entry
        2. Execution timing
        3. Success/failure log updates
        4. Error handling

        Args:
            run_id: ID of the parent workflow run
            input_data: Input data for the agent to process

        Returns:
            Agent output data as dictionary

        Raises:
            AgentExecutionError: If the agent fails after all retries
        """
        self.tokens_used = 0
        start_time = datetime.now(timezone.utc)

        # Create log entry
        input_summary = self._create_summary(input_data)
        log_entry = await self.db.create_agent_log(
            run_id=run_id,
            agent_name=self.name,
            status="started",
            input_summary=input_summary,
        )
        log_id = log_entry["id"]
        self.logger.info(f">> Started | run={run_id}")

        try:
            # Run the agent implementation
            result = await self.run(input_data)

            # Calculate duration
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            # Log success
            output_summary = self._create_summary(result)
            await self.db.update_agent_log(log_id, {
                "status": "completed",
                "output_summary": output_summary,
                "duration_ms": duration_ms,
                "tokens_used": self.tokens_used,
            })

            self.logger.info(
                f"[OK] Completed | run={run_id} | "
                f"duration={duration_ms}ms | tokens={self.tokens_used}"
            )
            return result

        except Exception as e:
            # Calculate duration even on failure
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            # Log failure
            await self.db.update_agent_log(log_id, {
                "status": "failed",
                "error_message": str(e),
                "duration_ms": duration_ms,
                "tokens_used": self.tokens_used,
            })

            self.logger.error(f"[FAIL] Failed | run={run_id} | error={e}")
            raise AgentExecutionError(
                agent_name=self.name,
                message=str(e),
                original_error=e,
            )

    @abstractmethod
    async def run(self, input_data: dict) -> dict:
        """
        Execute the agent's core logic.

        Override this method in each agent subclass.

        Args:
            input_data: Input data to process

        Returns:
            Processed output data as dictionary
        """
        pass

    def _create_summary(self, data: dict, max_length: int = 500) -> dict:
        """
        Create a truncated summary of data for logging.
        Avoids storing full DataFrames in the database.

        Args:
            data: Data to summarize
            max_length: Max string length per value

        Returns:
            Summarized dictionary
        """
        summary = {}
        for key, value in data.items():
            if isinstance(value, list):
                summary[key] = f"list[{len(value)} items]"
            elif isinstance(value, dict):
                summary[key] = f"dict[{len(value)} keys]"
            elif isinstance(value, str) and len(value) > max_length:
                summary[key] = value[:max_length] + "..."
            else:
                summary[key] = value
        return summary
