"""
Self-Healing Selector System

When a selector breaks (VTU portal updates their HTML), this system:
1. Tries all known selector variants
2. Falls back to heuristic DOM analysis (find by label text, placeholder, role)
3. Learns from successful selectors and persists them to disk
4. Auto-recovers without code changes

Also implements stealth measures to avoid bot detection.
"""

import json
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

logger = logging.getLogger(__name__)

# Where we persist learned selectors
SELECTOR_CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "selector_cache.json"


class SelfHealingLocator:
    """
    Intelligent element locator that self-heals when selectors break.

    Usage (Selenium):
        locator = SelfHealingLocator(driver, wait)
        element = locator.find("email_field")

    Usage (Playwright):
        locator = SelfHealingLocator(page=page)
        element = await locator.find_async("email_field")
    """

    # Known selector strategies for each logical field
    SELECTOR_DB: Dict[str, List[Dict[str, str]]] = {
        "email_field": [
            {"css": "input[autocomplete='email']"},
            {"css": "input[type='email']"},
            {"css": "input#email"},
            {"css": "input[name='email']"},
            {"css": "input[placeholder*='email' i]"},
            {"css": "input[placeholder*='Email']"},
            {"xpath": "//label[contains(text(),'Email')]/following::input[1]"},
            {"xpath": "//input[@type='text' and contains(@class,'email')]"},
        ],
        "password_field": [
            {"css": "input[autocomplete='current-password']"},
            {"css": "input[autocomplete='new-password']"},
            {"css": "input[type='password']"},
            {"css": "input#password"},
            {"css": "input[name='password']"},
            {"xpath": "//label[contains(text(),'Password')]/following::input[1]"},
        ],
        "login_button": [
            {"css": "button[type='submit']"},
            {"css": "button.login-btn"},
            {"css": "input[type='submit']"},
            {"xpath": "//button[contains(text(),'Sign')]"},
            {"xpath": "//button[contains(text(),'Log')]"},
            {"xpath": "//button[contains(text(),'Submit')]"},
        ],
        "description_field": [
            {"css": "textarea[name='description']"},
            {"css": "textarea[name='entry_text']"},
            {"css": "textarea[name='activities']"},
            {"xpath": "//label[contains(text(),'Description')]/following::textarea[1]"},
            {"xpath": "//label[contains(text(),'Activit')]/following::textarea[1]"},
            {"css": "textarea.form-control:first-of-type"},
            {"css": "div[data-field='description'] textarea"},
        ],
        "hours_field": [
            {"css": "input[name='hours']"},
            {"css": "input[type='number']"},
            {"xpath": "//label[contains(text(),'Hours')]/following::input[1]"},
            {"xpath": "//label[contains(text(),'Duration')]/following::input[1]"},
            {"css": "input[placeholder*='hours' i]"},
        ],
        "learnings_field": [
            {"css": "textarea[name='learnings']"},
            {"xpath": "//label[contains(text(),'Learning')]/following::textarea[1]"},
            {"xpath": "//label[contains(text(),'learning')]/following::textarea[1]"},
            {"css": "div[data-field='learnings'] textarea"},
        ],
        "blockers_field": [
            {"css": "textarea[name='blockers']"},
            {"xpath": "//label[contains(text(),'Blocker')]/following::textarea[1]"},
            {"xpath": "//label[contains(text(),'Challenge')]/following::textarea[1]"},
            {"css": "div[data-field='blockers'] textarea"},
        ],
        "links_field": [
            {"css": "input[name='links']"},
            {"xpath": "//label[contains(text(),'Link')]/following::input[1]"},
            {"xpath": "//label[contains(text(),'Reference')]/following::input[1]"},
            {"css": "input[placeholder*='link' i]"},
        ],
        "skills_input": [
            {"css": "input[id^='react-select-']"},
            {"css": ".react-select__input input"},
            {"css": "[class*='select'] input[role='combobox']"},
            {"xpath": "//div[contains(@class,'select')]//input"},
            {"css": "input[aria-autocomplete='list']"},
        ],
        "submit_button": [
            {"css": "button[type='submit']"},
            {"xpath": "//button[contains(text(),'Submit')]"},
            {"xpath": "//button[contains(text(),'Save')]"},
            {"css": "button.btn-primary"},
            {"css": "button.submit-btn"},
            {"xpath": "//button[contains(@class,'submit')]"},
        ],
        "date_picker": [
            {"css": "input[type='date']"},
            {"css": "button[aria-label*='date' i]"},
            {"css": ".react-datepicker__input-container input"},
            {"xpath": "//button[contains(@class,'calendar')]"},
            {"css": "[data-testid='date-picker']"},
        ],
        "internship_select": [
            {"css": "select[name='internship_id']"},
            {"css": "select#internship_id"},
            {"xpath": "//label[contains(text(),'Internship')]/following::select[1]"},
            {"css": "[data-field='internship'] select"},
        ],
    }

    def __init__(self, driver=None, wait=None, page=None):
        """
        Args:
            driver: Selenium WebDriver instance
            wait: Selenium WebDriverWait instance
            page: Playwright Page instance (for async mode)
        """
        self.driver = driver
        self.wait = wait
        self.page = page
        self._learned: Dict[str, str] = {}
        self._load_cache()

    def _load_cache(self):
        """Load previously successful selectors from disk."""
        try:
            if SELECTOR_CACHE_PATH.exists():
                self._learned = json.loads(SELECTOR_CACHE_PATH.read_text())
                logger.info(f"Loaded {len(self._learned)} cached selectors")
        except Exception as e:
            logger.warning(f"Failed to load selector cache: {e}")

    def _save_cache(self):
        """Persist successful selectors to disk."""
        try:
            SELECTOR_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            SELECTOR_CACHE_PATH.write_text(json.dumps(self._learned, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save selector cache: {e}")

    def find(self, field_name: str, timeout: float = 10.0) -> Any:
        """
        Find element using self-healing strategy (Selenium).

        1. Try cached/learned selector first
        2. Try all known selectors
        3. Fall back to heuristic search

        Returns the WebDriver element or raises.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        wait = self.wait or WebDriverWait(self.driver, timeout)

        # 1. Try learned selector first
        if field_name in self._learned:
            try:
                sel = self._learned[field_name]
                if sel.startswith("//"):
                    elem = wait.until(EC.presence_of_element_located((By.XPATH, sel)))
                else:
                    elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                logger.debug(f"[HEAL] Cache hit for '{field_name}': {sel}")
                return elem
            except Exception:
                logger.info(f"[HEAL] Cached selector broken for '{field_name}', searching...")
                del self._learned[field_name]

        # 2. Try all known selectors
        selectors = self.SELECTOR_DB.get(field_name, [])
        for sel_dict in selectors:
            for strategy, selector in sel_dict.items():
                try:
                    if strategy == "xpath":
                        elem = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        elem = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    # Success — learn this selector
                    self._learned[field_name] = selector
                    self._save_cache()
                    logger.info(f"[HEAL] Found '{field_name}' with: {selector}")
                    return elem
                except Exception:
                    continue

        # 3. Heuristic fallback — search by visible text
        elem = self._heuristic_find(field_name)
        if elem:
            return elem

        raise Exception(
            f"[HEAL] All selectors exhausted for '{field_name}'. "
            f"Tried {len(selectors)} strategies + heuristic."
        )

    def _heuristic_find(self, field_name: str) -> Any:
        """Last-resort heuristic: find elements by aria-label, placeholder, or nearby text."""
        from selenium.webdriver.common.by import By

        keywords = field_name.replace("_", " ").split()
        for kw in keywords:
            try:
                # Try aria-label
                elems = self.driver.find_elements(
                    By.CSS_SELECTOR, f"[aria-label*='{kw}' i]"
                )
                if elems:
                    logger.info(f"[HEAL] Heuristic found '{field_name}' via aria-label")
                    return elems[0]

                # Try placeholder
                elems = self.driver.find_elements(
                    By.CSS_SELECTOR, f"[placeholder*='{kw}' i]"
                )
                if elems:
                    logger.info(f"[HEAL] Heuristic found '{field_name}' via placeholder")
                    return elems[0]
            except Exception:
                continue

        return None

    async def find_async(self, field_name: str, timeout: float = 10000) -> Any:
        """
        Find element using self-healing strategy (Playwright async).

        Same logic as find() but for Playwright.
        """
        if not self.page:
            raise ValueError("Playwright page not provided")

        # 1. Try learned selector
        if field_name in self._learned:
            try:
                sel = self._learned[field_name]
                locator = self.page.locator(sel)
                await locator.wait_for(timeout=3000)
                logger.debug(f"[HEAL] Cache hit for '{field_name}': {sel}")
                return locator
            except Exception:
                logger.info(f"[HEAL] Cached selector broken for '{field_name}', searching...")
                del self._learned[field_name]

        # 2. Try all known selectors
        selectors = self.SELECTOR_DB.get(field_name, [])
        for sel_dict in selectors:
            for strategy, selector in sel_dict.items():
                try:
                    if strategy == "xpath":
                        locator = self.page.locator(f"xpath={selector}")
                    else:
                        locator = self.page.locator(selector)

                    await locator.wait_for(timeout=2000)
                    count = await locator.count()
                    if count > 0:
                        self._learned[field_name] = selector
                        self._save_cache()
                        logger.info(f"[HEAL] Found '{field_name}' with: {selector}")
                        return locator.first
                except Exception:
                    continue

        # 3. Heuristic — Playwright has great built-in heuristics
        keywords = field_name.replace("_", " ").replace("field", "").strip()
        try:
            locator = self.page.get_by_label(keywords)
            count = await locator.count()
            if count > 0:
                logger.info(f"[HEAL] Heuristic found '{field_name}' via label")
                return locator.first
        except Exception:
            pass

        try:
            locator = self.page.get_by_placeholder(keywords)
            count = await locator.count()
            if count > 0:
                logger.info(f"[HEAL] Heuristic found '{field_name}' via placeholder")
                return locator.first
        except Exception:
            pass

        raise Exception(
            f"[HEAL] All selectors exhausted for '{field_name}'. "
            f"Tried {len(selectors)} strategies + heuristic."
        )


def apply_stealth(driver) -> None:
    """
    Apply stealth measures to a Selenium WebDriver to avoid bot detection.

    Patches navigator.webdriver, injects realistic browser fingerprints,
    and removes automation indicators.
    """
    stealth_scripts = [
        # Remove webdriver flag
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",

        # Fake plugins
        """Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        })""",

        # Fake languages
        """Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'hi']
        })""",

        # Chrome runtime
        "window.chrome = { runtime: {} }",

        # Permissions
        """const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        )""",

        # WebGL vendor
        """const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.';
            if (parameter === 37446) return 'Intel Iris OpenGL Engine';
            return getParameter.call(this, parameter);
        }""",
    ]

    for script in stealth_scripts:
        try:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": script,
            })
        except Exception:
            # Fallback for non-Chrome drivers
            try:
                driver.execute_script(script)
            except Exception:
                pass

    logger.info("[STEALTH] Applied stealth patches to browser")


async def apply_stealth_playwright(page) -> None:
    """Apply stealth measures to a Playwright page."""
    await page.add_init_script("""
        // Remove webdriver flag
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

        // Fake plugins
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});

        // Fake languages
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'hi']});

        // Chrome runtime
        window.chrome = { runtime: {} };

        // Permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );
    """)
    logger.info("[STEALTH] Applied stealth patches to Playwright page")
