"""Centralized configuration management for VTU Diary Automation"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
SESSIONS_DIR = BASE_DIR / "sessions"
SYSTEM_PROMPTS_DIR = BASE_DIR / "system_prompts"

# Ensure directories exist
for dir_path in [DATA_DIR, LOGS_DIR, SCREENSHOTS_DIR, SESSIONS_DIR]:
    dir_path.mkdir(exist_ok=True)

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai, gemini, cerebras, groq, mock
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

# Browser Automation
BROWSER_ENGINE = os.getenv("BROWSER_ENGINE", "playwright")  # playwright or selenium
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
BROWSER_PROFILE = os.getenv("BROWSER_PROFILE", "default")
MAX_PARALLEL_BROWSERS = int(os.getenv("MAX_PARALLEL_BROWSERS", "2"))
SUBMISSION_DELAY_SECONDS = float(os.getenv("SUBMISSION_DELAY_SECONDS", "3.0"))

# VTU Portal
PORTAL_LOGIN_URL = os.getenv("PORTAL_LOGIN_URL", "https://internyet.vtu.ac.in")
VTU_USERNAME = os.getenv("VTU_EMAIL") or os.getenv("VTU_USERNAME")  # Support both
VTU_PASSWORD = os.getenv("VTU_PASSWORD")

# Date Management
DEFAULT_COUNTRY = os.getenv("DEFAULT_COUNTRY", "IN")  # For holiday calendar
SKIP_WEEKENDS = os.getenv("SKIP_WEEKENDS", "true").lower() == "true"
SKIP_HOLIDAYS = os.getenv("SKIP_HOLIDAYS", "true").lower() == "true"
MAX_DATE_RANGE_DAYS = int(os.getenv("MAX_DATE_RANGE_DAYS", "90"))

# AI Processing
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
BATCH_SIZE_DAYS = int(os.getenv("BATCH_SIZE_DAYS", "10"))  # Days per AI batch call (higher = fewer API calls)
DEFAULT_HOURS_PER_DAY = float(os.getenv("DEFAULT_HOURS_PER_DAY", "7.0"))
MIN_ENTRY_WORDS = int(os.getenv("MIN_ENTRY_WORDS", "120"))
MAX_ENTRY_WORDS = int(os.getenv("MAX_ENTRY_WORDS", "180"))

# Skills Database
SKILLS_DATABASE_PATH = DATA_DIR / "vtu_skills.json"
SKILLS_EMBEDDINGS_PATH = DATA_DIR / "skill_embeddings.npy"
SKILLS_INDEX_PATH = DATA_DIR / "skills_faiss.index"
SKILL_MATCH_THRESHOLD = float(os.getenv("SKILL_MATCH_THRESHOLD", "0.6"))

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'vtu_automation.db'}"
)

# API/Web
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "5000"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# Retry & Error Handling
MAX_SUBMISSION_RETRIES = int(os.getenv("MAX_SUBMISSION_RETRIES", "3"))
RETRY_BACKOFF_FACTOR = float(os.getenv("RETRY_BACKOFF_FACTOR", "2.0"))

# Audio/Video Processing
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium, large
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")

# Feature Flags
ENABLE_VERIFICATION = os.getenv("ENABLE_VERIFICATION", "true").lower() == "true"
ENABLE_SCREENSHOTS = os.getenv("ENABLE_SCREENSHOTS", "true").lower() == "true"
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
DRY_RUN_DEFAULT = os.getenv("DRY_RUN_DEFAULT", "false").lower() == "true"


def get_effective_setting(env_value, header_value=None):
    """Return header value (client-side) if provided, else env var.

    Priority: request header > environment variable
    """
    if header_value:
        return header_value
    return env_value
