"""Pydantic models for API requests/responses"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DiaryEntryPreview(BaseModel):
    """Preview of a single diary entry"""
    id: str = Field(description="Unique ID for this entry")
    date: str = Field(description="Date in YYYY-MM-DD format")
    hours: float = Field(description="Hours worked", ge=8.0, le=9.0)
    activities: str = Field(description="Activity description")
    learnings: str = Field(description="Learning summary")
    blockers: str = Field(default="None", description="Blockers or challenges")
    links: str = Field(default="", description="Related links")
    skills: List[str] = Field(description="Selected skills")
    confidence: float = Field(description="Confidence score 0-1", ge=0.0, le=1.0)
    editable: bool = Field(default=True, description="Whether entry can be edited")


class PlausibilityEntryScore(BaseModel):
    """Per-entry plausibility score"""
    date: str
    score: float
    flags: List[str] = []


class PlausibilityReport(BaseModel):
    """Batch plausibility analysis"""
    overall_score: float
    avg_confidence: float
    flags: List[str] = []
    entry_scores: List[PlausibilityEntryScore] = []


class GeneratePreviewRequest(BaseModel):
    """Request for generating preview entries"""
    date_range: str
    skip_weekends: bool = True
    skip_holidays: bool = True


class GeneratePreviewResponse(BaseModel):
    """Response with preview entries"""
    session_id: str
    entries: List[DiaryEntryPreview]
    total_entries: int
    high_confidence_count: int
    needs_review_count: int
    warnings: List[str] = []
    plausibility_report: Optional[Dict[str, Any]] = None


class ApproveAndSubmitRequest(BaseModel):
    """Request to approve and submit entries"""
    session_id: str
    approved_entries: List[DiaryEntryPreview]
    dry_run: bool = False


class SubmissionProgress(BaseModel):
    """Submission progress status"""
    total: int
    completed: int
    failed: int
    current: str
    status: str  # processing, completed, failed
