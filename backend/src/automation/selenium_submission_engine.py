"""Selenium-based parallel submission engine using ThreadPoolExecutor"""
import time
from typing import List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.selenium_submit import VTUSubmitter
from config import (
    MAX_PARALLEL_BROWSERS,
    SUBMISSION_DELAY_SECONDS,
    HEADLESS,
    SCREENSHOTS_DIR,
    ENABLE_SCREENSHOTS,
    PORTAL_LOGIN_URL
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SeleniumSubmissionEngine:
    """
    Selenium-based parallel submission engine.

    Uses ThreadPoolExecutor for concurrent submissions with multiple browser instances.
    """

    def __init__(self, max_workers: int = MAX_PARALLEL_BROWSERS, headless: bool = HEADLESS, credentials: Dict[str, Optional[str]] = None):
        self.max_workers = max_workers
        self.headless = headless
        self.credentials = credentials or {}
        self.results = []

        logger.info(f"Selenium engine initialized: {max_workers} workers, headless={headless}")

    def submit_bulk(self, entries: List[Dict[str, Any]], progress_tracker: Dict = None) -> List[Dict[str, Any]]:
        """
        Submit multiple diary entries concurrently using ThreadPoolExecutor.

        Args:
            entries: List of entry dicts with date, hours, activities, etc.
            progress_tracker: Optional dict to update with progress

        Returns:
            List of result dicts with status and metadata
        """
        logger.info(f"Starting bulk submission: {len(entries)} entries")

        results = []

        # Use ThreadPoolExecutor for parallel Selenium instances
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all entries
            future_to_entry = {
                executor.submit(self._submit_single_entry, entry): entry
                for entry in entries
            }

            # Collect results as they complete
            for future in as_completed(future_to_entry):
                entry = future_to_entry[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Completed: {entry.get('date')} - {result.get('status')}")

                    # Update progress tracker if provided
                    if progress_tracker:
                        if result.get('status') == 'success':
                            progress_tracker['completed'] = progress_tracker.get('completed', 0) + 1
                        else:
                            progress_tracker['failed'] = progress_tracker.get('failed', 0) + 1

                        progress_tracker['current'] = f"Processed {entry.get('date')} - {result.get('status')}"

                except Exception as e:
                    logger.error(f"Failed: {entry.get('date')} - {e}")
                    results.append({
                        "date": entry.get("date", "unknown"),
                        "status": "failed",
                        "error": str(e),
                        "entry": entry
                    })

                    # Update progress tracker for failures
                    if progress_tracker:
                        progress_tracker['failed'] = progress_tracker.get('failed', 0) + 1
                        progress_tracker['current'] = f"Failed {entry.get('date')}: {str(e)}"

        logger.info(f"Bulk submission complete: {len(results)} results")
        return results

    def _submit_single_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a single diary entry using Selenium"""
        date_str = entry.get("date", "unknown")
        submitter = None

        try:
            logger.info(f"Worker submitting: {date_str}")

            # Create Selenium driver instance for this thread
            submitter = VTUSubmitter(
                headless=self.headless,
                profile_name="default",
                wait_for_user=False
            )

            # Login to portal
            logger.info(f"Logging in for {date_str}")
            
            # Extract portal credentials
            username = self.credentials.get("portal_user") or VTU_USERNAME
            password = self.credentials.get("portal_pass") or VTU_PASSWORD
            
            # Check if we have credentials
            if not username or not password:
                raise Exception("Missing portal credentials (username/password)")

            submitter.login_manually(portal_url=PORTAL_LOGIN_URL, credentials=self.credentials)

            # Transform entry fields to match VTU form expectations
            # AI generates "activities" but form expects "description"
            form_entry = {
                "date": entry.get("date"),
                "hours": entry.get("hours", 7.0),
                "description": entry.get("activities", ""),  # Map activities -> description
                "learnings": entry.get("learnings", ""),
                "blockers": entry.get("blockers", "None"),
                "links": entry.get("links", ""),
                "skills": entry.get("skills", ["Git"])
            }

            # Submit entry
            logger.info(f"Submitting entry for {date_str}")
            success = submitter.fill_diary(form_entry, dry_run=False)

            # Rate limiting
            time.sleep(SUBMISSION_DELAY_SECONDS)

            return {
                "date": date_str,
                "status": "success" if success else "failed",
                "submitted_at": datetime.now().isoformat(),
                "entry": entry
            }

        except Exception as e:
            logger.error(f"Submission failed for {date_str}: {e}")
            return {
                "date": date_str,
                "status": "failed",
                "error": str(e),
                "submitted_at": datetime.now().isoformat(),
                "entry": entry
            }

        finally:
            if submitter:
                try:
                    submitter.close()
                except:
                    pass
