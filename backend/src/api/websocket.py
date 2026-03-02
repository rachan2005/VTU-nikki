"""WebSocket support for real-time progress updates"""
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming progress updates.

    Usage:
        ws://localhost:5000/ws/progress/{session_id}
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: {session_id}")

    try:
        # Import here to avoid circular dependency
        from .routes import progress_trackers

        while session_id in progress_trackers:
            tracker = progress_trackers[session_id]

            # Send progress update
            await websocket.send_json(tracker)

            # Check if complete
            if tracker.get("status") in ["completed", "failed"]:
                break

            # Wait before next update
            await asyncio.sleep(0.5)

        # Send final update
        if session_id in progress_trackers:
            await websocket.send_json(progress_trackers[session_id])

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")

    finally:
        await websocket.close()
