"""
Global error handling middleware and utilities.
"""

import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from backend.utils.logger import get_logger

logger = get_logger("error_handler")


class AgentExecutionError(Exception):
    """Raised when an agent fails during execution."""

    def __init__(self, agent_name: str, message: str, original_error: Exception | None = None):
        self.agent_name = agent_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{agent_name}] {message}")


class WorkflowError(Exception):
    """Raised when the workflow orchestration fails."""

    def __init__(self, run_id: str, message: str, step: str | None = None):
        self.run_id = run_id
        self.message = message
        self.step = step
        super().__init__(f"Workflow {run_id} failed at {step}: {message}")


class DataValidationError(Exception):
    """Raised when input data fails validation."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again.",
            "detail": str(exc) if True else None,  # Only in debug mode
        },
    )


async def agent_exception_handler(request: Request, exc: AgentExecutionError) -> JSONResponse:
    """Handler for agent execution errors."""
    logger.error(f"Agent error [{exc.agent_name}]: {exc.message}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "agent_execution_error",
            "agent": exc.agent_name,
            "message": exc.message,
        },
    )


async def validation_exception_handler(request: Request, exc: DataValidationError) -> JSONResponse:
    """Handler for data validation errors."""
    logger.warning(f"Validation error: {exc.message} — {exc.details}")

    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": exc.message,
            "details": exc.details,
        },
    )
