"""SQLAlchemy database models"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class SubmissionHistory(Base):
    """Track all diary submissions"""

    __tablename__ = "submission_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    hours = Column(Float, nullable=False)
    activities = Column(Text, nullable=False)
    learnings = Column(Text)
    blockers = Column(Text)
    links = Column(Text)
    skills = Column(JSON)  # List of skill names
    status = Column(String(20), nullable=False)  # success, failed, pending
    confidence_score = Column(Float)
    error_message = Column(Text)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    entry_metadata = Column(JSON)  # Additional metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)

    def __repr__(self):
        return f"<Submission {self.date} - {self.status}>"

    @classmethod
    def create(cls, session: Session, **kwargs) -> "SubmissionHistory":
        """Create new submission record"""
        submission = cls(**kwargs)
        session.add(submission)
        session.commit()
        return submission

    @classmethod
    def get_by_date(cls, session: Session, date: str) -> Optional["SubmissionHistory"]:
        """Get submission by date"""
        return session.query(cls).filter_by(date=date).first()

    @classmethod
    def get_month(cls, session: Session, year: int, month: int) -> List["SubmissionHistory"]:
        """Get all submissions for a month"""
        date_prefix = f"{year:04d}-{month:02d}"
        return session.query(cls).filter(cls.date.like(f"{date_prefix}%")).all()


class SkillCache(Base):
    """Cache skill matching results"""

    __tablename__ = "skill_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String(500), nullable=False, unique=True, index=True)
    matched_skills = Column(JSON)  # List of matched skill names
    similarity_scores = Column(JSON)  # Corresponding scores
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SkillCache '{self.query[:30]}...'>"

    @classmethod
    def get(cls, session: Session, query: str) -> Optional["SkillCache"]:
        """Get cached result"""
        return session.query(cls).filter_by(query=query).first()

    @classmethod
    def set(cls, session: Session, query: str, skills: List[str], scores: List[float]):
        """Cache skill matching result"""
        existing = cls.get(session, query)
        if existing:
            existing.matched_skills = skills
            existing.similarity_scores = scores
            existing.updated_at = datetime.utcnow()
        else:
            cache_entry = cls(
                query=query,
                matched_skills=skills,
                similarity_scores=scores
            )
            session.add(cache_entry)
        session.commit()


class ProcessingQueue(Base):
    """Queue for pending bulk processing jobs"""

    __tablename__ = "processing_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(50), nullable=False, unique=True, index=True)
    input_type = Column(String(50))  # text, audio, excel, etc.
    input_data = Column(JSON)
    target_dates = Column(JSON)  # List of dates
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    result = Column(JSON)  # Results when complete
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    def __repr__(self):
        return f"<ProcessingQueue {self.job_id} - {self.status}>"


class AppSettings(Base):
    """Application settings (single row, id=1)"""

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, default=1)

    # LLM API Keys
    openai_api_key = Column(String(500), nullable=True)
    gemini_api_key = Column(String(500), nullable=True)
    cerebras_api_key = Column(String(500), nullable=True)
    groq_api_key = Column(String(500), nullable=True)
    llm_provider = Column(String(50), default="auto")

    # Portal Credentials
    vtu_username = Column(String(200), nullable=True)
    vtu_password = Column(String(500), nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls, session: Session) -> "AppSettings":
        settings = session.query(cls).filter_by(id=1).first()
        if not settings:
            settings = cls(id=1)
            session.add(settings)
            session.commit()
        return settings

    @classmethod
    def update(cls, session: Session, **kwargs) -> "AppSettings":
        settings = cls.get(session)
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        session.commit()
        return settings
