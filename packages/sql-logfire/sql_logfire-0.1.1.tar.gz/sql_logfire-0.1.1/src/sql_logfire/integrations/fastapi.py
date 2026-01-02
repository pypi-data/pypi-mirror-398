from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from ..core import LogFire
from ..dashboard import html_template

def create_logfire_router(logfire_instance: LogFire):
    """
    Creates a FastAPI Router containing the Dashboard and API.
    Usage: app.include_router(create_logfire_router(logfire), prefix="/logfire")
    """
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    async def get_dashboard():
        return html_template

    @router.get("/api/logs")
    async def get_logs_api(minutes: int = 0, q: str = ""):
        logs = logfire_instance.get_logs(minutes=minutes, query_str=q)
        return [
            {
                "id": l.id,
                "level": l.level,
                "message": l.message,
                "created_at": l.created_at.isoformat()
            } 
            for l in logs
        ]

    return router