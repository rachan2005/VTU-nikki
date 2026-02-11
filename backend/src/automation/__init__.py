"""Browser automation — Playwright-first with Selenium fallback"""
from .retry_logic import RetryStrategy

try:
    from .submission_engine import PlaywrightSubmissionEngine as ParallelSubmissionEngine
except ImportError:
    from .selenium_submission_engine import SeleniumSubmissionEngine as ParallelSubmissionEngine

__all__ = ["ParallelSubmissionEngine", "RetryStrategy"]
