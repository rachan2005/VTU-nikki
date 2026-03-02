"""VTU Diary Automation v3.0 — GOD MODE

FastAPI backend serving:
  - /api/*  → REST endpoints for upload, preview, submit, history
  - /ws/*   → WebSocket for real-time progress
  - /*      → React SPA (built to /static) with SPA fallback
"""
import sys
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Fix for Windows asyncio + Playwright subprocess issue
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from src.api import router, websocket_endpoint
from src.db import init_db
from config import API_HOST, API_PORT, DEBUG_MODE
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Static dir is in parent (root) directory
STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("Starting VTU Diary Automation v3.0 — GOD MODE")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down VTU Diary Automation")


# Create FastAPI app with lifespan handler
app = FastAPI(
    title="VTU Diary Automation",
    description="GOD MODE — AI diary generation + parallel browser swarm submission",
    version="3.0.0",
    lifespan=lifespan,
)

# CORS middleware (allows React dev server at :3000 to talk to API at :5000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes (/api/*)
app.include_router(router)


@app.websocket("/ws/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for progress updates"""
    await websocket_endpoint(websocket, session_id)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "3.0.0", "mode": "god"}


# Serve React SPA — mount static assets if build exists
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_spa(request: Request, full_path: str):
        """SPA fallback: serve index.html for all non-API routes"""
        # Don't intercept API or WebSocket routes
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            return
        # Try to serve the exact file first (css, js, images)
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Fallback to index.html for client-side routing
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return HTMLResponse("<h1>Build the frontend first: cd frontend && npm run build</h1>")
else:
    @app.get("/", response_class=HTMLResponse)
    async def no_build():
        return HTMLResponse(
            "<div style='font-family:system-ui;padding:60px;text-align:center'>"
            "<h1>VTU Diary v3.0 — GOD MODE</h1>"
            "<p>Frontend not built yet. Run:</p>"
            "<pre style='background:#111;color:#0f0;padding:20px;border-radius:8px;display:inline-block'>"
            "cd frontend && npm install && npm run build"
            "</pre>"
            "<p style='margin-top:20px;color:#888'>Or run <code>npm run dev</code> for development at :3000</p>"
            "</div>"
        )


if __name__ == '__main__':
    import uvicorn

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    uvicorn.run(
        "app:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        reload_dirs=[".", "src"],
        log_level="info",
        loop="asyncio",
    )
