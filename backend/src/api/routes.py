"""FastAPI routes for bulk submission with approval workflow"""
import uuid
import asyncio
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from src.input import InputRouter, normalize_input_data
from src.date_management import DateManager
from src.ai.agent import DiaryGenerationAgent
from src.automation import ParallelSubmissionEngine
from src.db import get_db, SubmissionHistory
from src.plausibility import PlausibilityEngine
from config import get_effective_setting
import config as app_config
from .models import (
    DiaryEntryPreview,
    GeneratePreviewResponse,
    ApproveAndSubmitRequest,
    SubmissionProgress
)
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Global storage
progress_trackers = {}
preview_sessions = {}  # Store generated entries before approval


def extract_credentials(request: Request) -> Dict[str, Optional[str]]:
    """Extract client-side credentials from request headers.

    Headers sent by frontend (from localStorage):
      X-Groq-Key, X-Gemini-Key, X-Cerebras-Key, X-Openai-Key,
      X-LLM-Provider, X-Portal-User, X-Portal-Pass

    Returns effective values: header > env var.
    """
    return {
        "groq_api_key": get_effective_setting(
            app_config.GROQ_API_KEY, request.headers.get("x-groq-key")
        ),
        "gemini_api_key": get_effective_setting(
            app_config.GEMINI_API_KEY, request.headers.get("x-gemini-key")
        ),
        "cerebras_api_key": get_effective_setting(
            app_config.CEREBRAS_API_KEY, request.headers.get("x-cerebras-key")
        ),
        "openai_api_key": get_effective_setting(
            app_config.OPENAI_API_KEY, request.headers.get("x-openai-key")
        ),
        "llm_provider": get_effective_setting(
            app_config.LLM_PROVIDER, request.headers.get("x-llm-provider")
        ),
        "portal_user": get_effective_setting(
            app_config.VTU_USERNAME, request.headers.get("x-portal-user")
        ),
        "portal_pass": get_effective_setting(
            app_config.VTU_PASSWORD, request.headers.get("x-portal-pass")
        ),
    }


class BulkSubmitResponse(BaseModel):
    session_id: str
    total_entries: int
    message: str


class UploadResponse(BaseModel):
    """Response after file upload"""
    upload_id: str
    file_name: str
    file_size: int
    message: str


@router.post("/api/upload-file", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Step 1: Upload file and get upload ID.

    Returns upload_id to be used in generate-preview
    """
    try:
        # Generate upload ID
        upload_id = str(uuid.uuid4())

        # Save to temp directory
        temp_dir = Path(tempfile.gettempdir()) / "vtu_uploads"
        temp_dir.mkdir(exist_ok=True)

        file_path = temp_dir / f"{upload_id}_{file.filename}"

        # Save uploaded file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Store file info
        preview_sessions[upload_id] = {
            "file_path": str(file_path),
            "file_name": file.filename,
            "file_size": len(content),
            "uploaded_at": asyncio.get_event_loop().time()
        }

        logger.info(f"File uploaded: {file.filename} ({len(content)} bytes)")

        return UploadResponse(
            upload_id=upload_id,
            file_name=file.filename,
            file_size=len(content),
            message="File uploaded successfully"
        )

    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/upload-text", response_model=UploadResponse)
async def upload_text(text: str = Form(...)):
    """
    Step 1 (Alternative): Upload text content directly.

    Returns upload_id to be used in generate-preview
    """
    try:
        # Generate upload ID
        upload_id = str(uuid.uuid4())

        # Save to temp directory as .txt file
        temp_dir = Path(tempfile.gettempdir()) / "vtu_uploads"
        temp_dir.mkdir(exist_ok=True)

        file_path = temp_dir / f"{upload_id}_input.txt"

        # Save text content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

        # Store file info
        preview_sessions[upload_id] = {
            "file_path": str(file_path),
            "file_name": "text_input.txt",
            "file_size": len(text.encode('utf-8')),
            "uploaded_at": asyncio.get_event_loop().time(),
            "input_type": "text"
        }

        logger.info(f"Text uploaded: {len(text)} characters")

        return UploadResponse(
            upload_id=upload_id,
            file_name="text_input.txt",
            file_size=len(text.encode('utf-8')),
            message="Text uploaded successfully"
        )

    except Exception as e:
        logger.error(f"Text upload failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/generate-preview", response_model=GeneratePreviewResponse)
async def generate_preview(
    request: Request,
    upload_id: str = Form(...),
    date_range: str = Form(...),
    skip_weekends: bool = Form(True),
    skip_holidays: bool = Form(True)
):
    """
    Step 2: Generate diary entries for preview (no submission).

    Returns preview entries for user approval.
    """
    try:
        # Get uploaded file info
        if upload_id not in preview_sessions:
            raise HTTPException(status_code=404, detail="Upload not found")

        session = preview_sessions[upload_id]
        file_path = session["file_path"]

        # Process input
        logger.info(f"Processing input: {session['file_name']}")
        router_obj = InputRouter()
        input_data = router_obj.process(file_path)
        normalized = normalize_input_data(input_data)

        # Parse dates
        date_manager = DateManager(skip_weekends=skip_weekends, skip_holidays=skip_holidays)
        dates = date_manager.parse_date_input(date_range)

        logger.info(f"Generating entries for {len(dates)} dates")

        # Generate entries with AI (pass client-side credentials)
        creds = extract_credentials(request)
        agent = DiaryGenerationAgent(credentials=creds)

        if len(normalized) == 1:
            result = agent.generate_bulk(normalized[0]["raw_text"], dates)
        else:
            result = agent.generate_bulk(normalized, dates)

        # Filter by confidence
        filtered = agent.filter_by_confidence(result)
        high_confidence = filtered["auto_submit"]
        needs_review = filtered["manual_review"]

        # Convert to preview format
        preview_entries = []
        for entry in result.entries:
            preview_entries.append(DiaryEntryPreview(
                id=str(uuid.uuid4()),
                date=entry.date,
                hours=entry.hours,
                activities=entry.activities,
                learnings=entry.learnings,
                blockers=entry.blockers,
                links=entry.links,
                skills=entry.skills,
                confidence=entry.confidence,
                editable=True
            ))

        # Run plausibility analysis
        plausibility = PlausibilityEngine()
        plausibility_report = plausibility.score_batch(
            [e.dict() for e in preview_entries]
        )

        # Create session for approval
        session_id = str(uuid.uuid4())
        preview_sessions[session_id] = {
            "entries": [e.dict() for e in preview_entries],
            "original_upload_id": upload_id,
            "warnings": result.warnings,
            "plausibility_report": plausibility_report
        }

        logger.info(
            f"Preview generated: {len(preview_entries)} entries, "
            f"plausibility={plausibility_report['overall_score']:.2f}"
        )

        return GeneratePreviewResponse(
            session_id=session_id,
            entries=preview_entries,
            total_entries=len(preview_entries),
            high_confidence_count=len(high_confidence),
            needs_review_count=len(needs_review),
            warnings=result.warnings,
            plausibility_report=plausibility_report
        )

    except Exception as e:
        logger.error(f"Preview generation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/approve-and-submit")
async def approve_and_submit(
    raw_request: Request,
    request: ApproveAndSubmitRequest,
    background_tasks: BackgroundTasks
):
    """
    Step 3: User approves entries → submit to portal.

    Submits approved entries in background, returns progress session.
    """
    try:
        session_id = request.session_id

        # Validate session
        if session_id not in preview_sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        # Extract client-side portal credentials
        creds = extract_credentials(raw_request)

        # Create progress tracker
        progress_id = str(uuid.uuid4())
        progress_trackers[progress_id] = {
            "total": len(request.approved_entries),
            "completed": 0,
            "failed": 0,
            "current": "Starting submission...",
            "status": "processing"
        }

        # Start background submission with credentials
        background_tasks.add_task(
            submit_approved_entries,
            progress_id,
            request.approved_entries,
            request.dry_run,
            creds
        )

        return {
            "progress_id": progress_id,
            "total_entries": len(request.approved_entries),
            "message": "Submission started",
            "dry_run": request.dry_run
        }

    except Exception as e:
        logger.error(f"Approval submission failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/submit-bulk", response_model=BulkSubmitResponse)
async def submit_bulk(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    date_range: str = Form(...),
    skip_weekends: bool = Form(True),
    skip_holidays: bool = Form(True),
    dry_run: bool = Form(False)
):
    """
    Bulk submission endpoint.

    Args:
        file: Input file (Excel, PDF, audio, etc.)
        date_range: Date range string (e.g., "2025-01-01 to 2025-01-31")
        skip_weekends: Skip weekends
        skip_holidays: Skip holidays
        dry_run: Generate without submitting

    Returns:
        Session ID for progress tracking
    """
    session_id = str(uuid.uuid4())

    try:
        # Save uploaded file temporarily
        temp_file = f"/tmp/{file.filename}"
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)

        # Parse dates
        date_manager = DateManager(skip_weekends=skip_weekends, skip_holidays=skip_holidays)
        dates = date_manager.parse_date_input(date_range)

        # Initialize progress tracker
        progress_trackers[session_id] = {
            "total": len(dates),
            "completed": 0,
            "failed": 0,
            "current": "Starting...",
            "status": "processing"
        }

        # Start background task
        background_tasks.add_task(
            process_bulk_task,
            session_id,
            temp_file,
            dates,
            dry_run
        )

        return BulkSubmitResponse(
            session_id=session_id,
            total_entries=len(dates),
            message=f"Processing {len(dates)} entries"
        )

    except Exception as e:
        logger.error(f"Bulk submit failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/progress/{session_id}")
async def get_progress(session_id: str):
    """Get progress for a bulk submission session"""
    if session_id not in progress_trackers:
        raise HTTPException(status_code=404, detail="Session not found")

    return progress_trackers[session_id]


@router.get("/api/history")
async def get_history(
    limit: int = 50,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """
    Get submission history with optional filters.

    Args:
        limit: Maximum number of records to return (default 50)
        status: Filter by status (success, failed, pending)
        date_from: Filter from date (YYYY-MM-DD)
        date_to: Filter to date (YYYY-MM-DD)

    Returns:
        List of submission history records
    """
    try:
        db = get_db()

        try:
            query = db.query(SubmissionHistory)

            # Apply filters
            if status:
                query = query.filter(SubmissionHistory.status == status)

            if date_from:
                query = query.filter(SubmissionHistory.date >= date_from)

            if date_to:
                query = query.filter(SubmissionHistory.date <= date_to)

            # Order by most recent first and limit
            submissions = query.order_by(
                SubmissionHistory.submitted_at.desc()
            ).limit(limit).all()

            # Convert to dict for JSON response
            results = []
            for sub in submissions:
                results.append({
                    "id": sub.id,
                    "date": sub.date,
                    "hours": sub.hours,
                    "activities": sub.activities,
                    "learnings": sub.learnings,
                    "blockers": sub.blockers,
                    "links": sub.links,
                    "skills": sub.skills,
                    "status": sub.status,
                    "confidence_score": sub.confidence_score,
                    "error_message": sub.error_message,
                    "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else None
                })

            return {
                "total": len(results),
                "submissions": results
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/history/stats")
async def get_history_stats():
    """Get statistics about submission history"""
    try:
        db = get_db()

        try:
            total = db.query(SubmissionHistory).count()
            successful = db.query(SubmissionHistory).filter(
                SubmissionHistory.status == "success"
            ).count()
            failed = db.query(SubmissionHistory).filter(
                SubmissionHistory.status == "failed"
            ).count()

            return {
                "total_submissions": total,
                "successful": successful,
                "failed": failed,
                "success_rate": round((successful / total * 100) if total > 0 else 0, 2)
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to fetch stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_bulk_task(session_id: str, file_path: str, dates: list, dry_run: bool):
    """Background task for bulk processing (legacy direct submission)"""
    tracker = progress_trackers[session_id]

    try:
        # Process input
        tracker["current"] = "Processing input file..."
        router_obj = InputRouter()
        input_data = router_obj.process(file_path)
        normalized = normalize_input_data(input_data)

        # Generate entries
        tracker["current"] = "Generating diary entries with AI..."
        agent = DiaryGenerationAgent()

        if len(normalized) == 1:
            result = agent.generate_bulk(normalized[0]["raw_text"], dates)
        else:
            result = agent.generate_bulk(normalized, dates)

        if dry_run:
            tracker["status"] = "completed"
            tracker["current"] = "Dry run complete"
            tracker["completed"] = len(result.entries)
            return

        # Submit
        tracker["current"] = "Submitting to portal..."
        engine = ParallelSubmissionEngine()
        entries_dict = [e.dict() for e in result.entries]

        # Update progress during submission
        for i, entry in enumerate(entries_dict):
            tracker["current"] = f"Submitting {entry['date']}..."
            # Actual submission would happen here
            await asyncio.sleep(0.1)  # Simulate
            tracker["completed"] += 1

        tracker["status"] = "completed"
        tracker["current"] = "All done!"

    except Exception as e:
        logger.error(f"Bulk processing failed: {e}")
        tracker["status"] = "failed"
        tracker["current"] = f"Error: {str(e)}"


async def submit_approved_entries(
    progress_id: str,
    entries: list[DiaryEntryPreview],
    dry_run: bool,
    credentials: Dict[str, Optional[str]] = None
):
    """Background task for submitting approved entries"""
    tracker = progress_trackers[progress_id]

    try:
        if dry_run:
            # Simulate dry run
            for entry in entries:
                tracker["current"] = f"Dry run: {entry.date}"
                await asyncio.sleep(0.1)
                tracker["completed"] += 1

            tracker["status"] = "completed"
            tracker["current"] = "Dry run complete - No entries submitted"
            return

        # Convert to dict format for engine
        entries_dict = [e.dict() for e in entries]

        # Create submission engine with client-side credentials
        engine = ParallelSubmissionEngine(credentials=credentials)

        # Submit in background with progress updates
        tracker["current"] = "Initializing browser sessions..."

        # Run synchronous Selenium submission in thread pool with progress tracking
        results = await asyncio.to_thread(engine.submit_bulk, entries_dict, tracker)

        # Get database session
        db = get_db()

        # Process results and save to database (tracker already updated by engine)
        try:
            for result in results:
                entry_data = result.get("entry", {})

                if result.get("status") == "success":
                    # Save successful submission to database
                    SubmissionHistory.create(
                        session=db,
                        date=entry_data.get("date"),
                        hours=entry_data.get("hours", 7.0),
                        activities=entry_data.get("activities", ""),
                        learnings=entry_data.get("learnings", ""),
                        blockers=entry_data.get("blockers", ""),
                        links=entry_data.get("links", ""),
                        skills=entry_data.get("skills", []),
                        status="success",
                        confidence_score=entry_data.get("confidence", 0.0),
                        submitted_at=datetime.fromisoformat(result.get("submitted_at")),
                        entry_metadata={"result": result}
                    )
                else:
                    # Save failed submission to database
                    SubmissionHistory.create(
                        session=db,
                        date=entry_data.get("date", "unknown"),
                        hours=entry_data.get("hours", 0.0),
                        activities=entry_data.get("activities", ""),
                        learnings=entry_data.get("learnings", ""),
                        blockers=entry_data.get("blockers", ""),
                        links=entry_data.get("links", ""),
                        skills=entry_data.get("skills", []),
                        status="failed",
                        confidence_score=entry_data.get("confidence", 0.0),
                        error_message=result.get("error", "Unknown error"),
                        entry_metadata={"result": result}
                    )
        finally:
            db.close()

        tracker["status"] = "completed"
        tracker["current"] = f"Complete! {tracker['completed']} succeeded, {tracker['failed']} failed"

    except Exception as e:
        logger.error(f"Submission task failed: {e}")
        tracker["status"] = "failed"
        tracker["current"] = f"Error: {str(e)}"
