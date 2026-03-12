from .workflows import router as workflows_router
from .reports import router as reports_router
from .approvals import router as approvals_router
from .dashboard import router as dashboard_router

__all__ = [
    "workflows_router",
    "reports_router",
    "approvals_router",
    "dashboard_router"
]
