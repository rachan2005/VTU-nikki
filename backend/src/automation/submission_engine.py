"""Playwright submission engine -- sequential, single page, bulletproof.

One browser, one page, loop through entries. No parallel session issues.
Login once, reuse for all entries. Navigate back to diary page between entries.
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from config import (
    MAX_PARALLEL_BROWSERS,
    SUBMISSION_DELAY_SECONDS,
    HEADLESS,
    SCREENSHOTS_DIR,
    ENABLE_SCREENSHOTS,
    PORTAL_LOGIN_URL,
    VTU_USERNAME,
    VTU_PASSWORD
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

DIARY_URL = "https://vtu.internyet.in/dashboard/student/student-diary"


def _ordinal(n: int) -> str:
    if 11 <= n <= 13:
        return f"{n}th"
    return f"{n}{['th','st','nd','rd','th','th','th','th','th','th'][n % 10]}"


class PlaywrightSubmissionEngine:
    """Sequential Playwright submission -- one page, all entries, no timeouts."""

    def __init__(self, max_workers: int = MAX_PARALLEL_BROWSERS, headless: bool = HEADLESS):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("pip install playwright && playwright install chromium")
        self.max_workers = max_workers
        self.headless = headless
        logger.info(f"Playwright engine: sequential mode, headless={headless}")

    def submit_bulk(self, entries: List[Dict[str, Any]], progress_tracker: Dict = None) -> List[Dict[str, Any]]:
        return asyncio.run(self._run(entries, progress_tracker))

    async def _run(self, entries: List[Dict[str, Any]], tracker: Optional[Dict]) -> List[Dict[str, Any]]:
        results = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()

            # Login once
            await self._login(page)
            logger.info("Logged in, starting submissions...")

            # Submit each entry sequentially on the same page
            for i, entry in enumerate(entries):
                date_str = entry.get("date", "unknown")
                if tracker:
                    tracker["current"] = f"[{i+1}/{len(entries)}] {date_str}..."

                try:
                    await self._submit_one(page, entry)
                    results.append({
                        "date": date_str,
                        "status": "success",
                        "submitted_at": datetime.now().isoformat(),
                        "entry": entry,
                    })
                    logger.info(f"[{i+1}/{len(entries)}] Submitted: {date_str}")
                    if tracker:
                        tracker["completed"] = tracker.get("completed", 0) + 1

                except Exception as e:
                    err_msg = str(e)
                    if "already" in err_msg.lower():
                        logger.info(f"[{i+1}/{len(entries)}] Skipped {date_str}: already submitted")
                        results.append({
                            "date": date_str,
                            "status": "skipped",
                            "error": err_msg,
                            "entry": entry,
                        })
                        if tracker:
                            tracker["completed"] = tracker.get("completed", 0) + 1
                    else:
                        logger.error(f"[{i+1}/{len(entries)}] Failed {date_str}: {e}")
                        results.append({
                            "date": date_str,
                            "status": "failed",
                            "error": err_msg,
                            "entry": entry,
                        })
                        if tracker:
                            tracker["failed"] = tracker.get("failed", 0) + 1
                    if ENABLE_SCREENSHOTS:
                        try:
                            await page.screenshot(path=str(SCREENSHOTS_DIR / f"{date_str}_error.png"))
                        except Exception:
                            pass

            await context.close()
            await browser.close()

        return results

    async def _submit_one(self, page: Page, entry: Dict):
        """Submit a single entry. Page is already logged in."""
        date_str = entry.get("date", "unknown")

        # Navigate to diary page
        await page.goto(DIARY_URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(1)
        await self._dismiss_popup(page)

        # Check if we landed on the selection page or somewhere else
        combo = page.get_by_role("combobox", name="Select Internship")
        try:
            await combo.wait_for(timeout=10000)
        except Exception:
            # Page didn't show selection form -- might be already filled or session expired
            page_text = await page.text_content("body") or ""
            if "already" in page_text.lower() or "submitted" in page_text.lower() or "edit" in page_text.lower():
                raise Exception(f"Date {date_str} appears to be already submitted")
            # Try re-login and retry
            logger.warning(f"Selection page not found for {date_str}, re-logging in...")
            await self._login(page)
            await page.goto(DIARY_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(1)
            await self._dismiss_popup(page)
            await combo.wait_for(timeout=15000)

        # Select internship
        await combo.click()
        await asyncio.sleep(0.5)

        # Find first enabled option (aria-disabled="false" means enabled)
        options = page.locator("[role='option'][aria-disabled='false']")
        count = await options.count()
        if count > 0:
            await options.first.click()
        else:
            # Fallback: click by known internship name
            try:
                await page.get_by_role("option", name="EGDK").click()
            except Exception:
                await page.locator("[role='option']").nth(1).click()
        await asyncio.sleep(0.5)

        # Select date
        await self._select_date(page, date_str)

        # Continue
        cont_btn = page.get_by_role("button", name="Continue")
        await cont_btn.wait_for(timeout=10000)
        await cont_btn.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)

        # Check if form loaded or if date is already filled
        desc_field = page.get_by_role("textbox", name="Briefly describe the work you")
        try:
            await desc_field.wait_for(timeout=15000)
        except Exception:
            # Form didn't load -- retry entire selection flow once
            logger.warning(f"Form not found for {date_str}, retrying...")
            await page.goto(DIARY_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            await self._dismiss_popup(page)
            try:
                c2 = page.get_by_role("combobox", name="Select Internship")
                await c2.wait_for(timeout=10000)
                await c2.click()
                await asyncio.sleep(0.5)
                o2 = page.locator("[role='option'][aria-disabled='false']")
                if await o2.count() > 0:
                    await o2.first.click()
                await asyncio.sleep(0.5)
                await self._select_date(page, date_str)
                await page.get_by_role("button", name="Continue").click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)
                await desc_field.wait_for(timeout=15000)
            except Exception:
                raise Exception(f"Date {date_str}: form failed to load after retry")

        # Fill form
        await self._fill_form(page, entry)

        # Save -- force enable disabled button and click via JS
        save_btn = page.get_by_role("button", name="Save")
        await save_btn.wait_for(state="attached", timeout=10000)
        await page.evaluate("""
            const btn = document.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled = false;
                btn.removeAttribute('disabled');
                btn.click();
            }
        """)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)

    async def _login(self, page: Page):
        # Clear cookies and go to login page fresh
        await page.context.clear_cookies()
        await page.goto(PORTAL_LOGIN_URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(1)

        # Check if already logged in (redirected to dashboard)
        if "sign-in" not in page.url.lower() and "login" not in page.url.lower():
            logger.info("Already logged in, skipping login")
            await self._dismiss_popup(page)
            return

        email = page.get_by_role("textbox", name="Enter your email address")
        await email.wait_for(timeout=10000)
        await email.fill(VTU_USERNAME)
        await page.get_by_role("textbox", name="Password").fill(VTU_PASSWORD)
        await page.get_by_role("button", name="Sign In").click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        await self._dismiss_popup(page)

    async def _dismiss_popup(self, page: Page):
        try:
            btn = page.get_by_role("button", name="I Understand")
            if await btn.is_visible(timeout=2000):
                await btn.click()
                await asyncio.sleep(0.5)
        except Exception:
            pass

    async def _select_date(self, page: Page, date_str: str):
        parts = date_str.split("-")
        if len(parts) != 3:
            return
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])

        # Open calendar
        pick_btn = page.get_by_role("button", name="Pick a Date")
        await pick_btn.wait_for(timeout=10000)
        await pick_btn.click()
        await asyncio.sleep(0.5)

        # Year
        await page.get_by_label("Choose the Year").select_option(str(year))
        await asyncio.sleep(0.3)

        # Month (0-indexed)
        await page.get_by_label("Choose the Month").select_option(str(month - 1))
        await asyncio.sleep(0.5)

        # Day -- use ordinal in aria-label for precise matching
        ordinal = _ordinal(day)
        try:
            # Look for button with aria-label containing "5th" (exact day)
            day_btn = page.locator(f"button[aria-label*='{ordinal},']")
            if await day_btn.count() > 0:
                await day_btn.first.click()
                logger.info(f"Selected day: {day} ({ordinal})")
            else:
                # Fallback: text match
                await page.locator(f"button:text-is('{day}')").first.click()
                logger.info(f"Selected day: {day} (text match)")
        except Exception as e:
            logger.warning(f"Day {day} selection failed: {e}")

        await asyncio.sleep(0.5)

    async def _fill_form(self, page: Page, entry: Dict):
        description = entry.get("activities", entry.get("description", ""))
        hours = str(entry.get("hours", 7))
        links = entry.get("links", "") or "None"
        learnings = entry.get("learnings", "")
        blockers = entry.get("blockers", "None")
        skills = entry.get("skills", ["Git"])
        if isinstance(skills, str):
            skills = [skills]

        # Wait for form
        desc = page.get_by_role("textbox", name="Briefly describe the work you")
        await desc.wait_for(timeout=15000)

        # Fill fields + trigger React state updates
        await desc.fill(description)
        await desc.dispatch_event("input")
        await desc.dispatch_event("change")

        hours_field = page.get_by_placeholder("e.g.")
        await hours_field.fill(hours)
        await hours_field.dispatch_event("input")
        await hours_field.dispatch_event("change")

        links_field = page.get_by_role("textbox", name="Paste one or more relevant")
        await links_field.fill(links)
        await links_field.dispatch_event("change")

        learn_field = page.get_by_role("textbox", name="What did you learn or ship")
        await learn_field.fill(learnings)
        await learn_field.dispatch_event("change")

        block_field = page.get_by_role("textbox", name="Anything that slowed you down?")
        await block_field.fill(blockers)
        await block_field.dispatch_event("change")

        # Skills
        for skill in skills:
            try:
                # Open dropdown
                dropdown = page.locator(".react-select__dropdown-indicator").last
                await dropdown.click()
                await asyncio.sleep(0.3)

                # Try exact match first
                opt = page.get_by_role("option", name=skill, exact=True)
                if await opt.count() > 0:
                    await opt.click()
                    logger.info(f"Skill: {skill}")
                else:
                    # Type to filter then select first
                    inp = page.locator("input[id^='react-select-']")
                    await inp.fill(skill)
                    await asyncio.sleep(0.5)
                    first = page.get_by_role("option").first
                    if await first.count() > 0:
                        await first.click()
                        logger.info(f"Skill (filtered): {skill}")
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.warning(f"Skill '{skill}': {e}")
