"""Browser automation — Playwright-first with Selenium fallback"""
from typing import List, Dict, Any, Optional
from .retry_logic import RetryStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ParallelSubmissionEngine:
    """ Smart wrapper that tries Playwright and falls back to Selenium on failure """
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._engine = None
        self._mode = "playwright"
        
        try:
            from .submission_engine import PlaywrightSubmissionEngine
            self._engine = PlaywrightSubmissionEngine(*args, **kwargs)
        except (ImportError, Exception) as e:
            logger.warning(f"Failed to initialize Playwright engine: {e}. Falling back to Selenium.")
            self._mode = "selenium"
            from .selenium_submission_engine import SeleniumSubmissionEngine
            self._engine = SeleniumSubmissionEngine(*args, **kwargs)

    def submit_bulk(self, entries: List[Dict[str, Any]], progress_tracker: Dict = None) -> List[Dict[str, Any]]:
        if self._mode == "playwright":
            try:
                return self._engine.submit_bulk(entries, progress_tracker)
            except Exception as e:
                logger.error(f"Playwright submission failed at runtime: {e}. Attempting manual fallback to Selenium.")
                # Runtime fallback
                from .selenium_submission_engine import SeleniumSubmissionEngine
                fallback_engine = SeleniumSubmissionEngine(*self.args, **self.kwargs)
                return fallback_engine.submit_bulk(entries, progress_tracker)
        else:
            return self._engine.submit_bulk(entries, progress_tracker)

__all__ = ["ParallelSubmissionEngine", "RetryStrategy"]
