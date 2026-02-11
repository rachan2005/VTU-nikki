"""Playwright-based VTU submitter."""
import os
from pathlib import Path
from .driver import setup_browser, close_browser
from .auth import login
from .form import fill_diary


class VTUSubmitterPlaywright:
    """Facade for VTU automation using Playwright."""

    SESSION_DIR = Path("sessions")

    def __init__(self, headless=False, profile_name="default"):
        self.headless = headless
        self.profile_name = profile_name
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # Initialize browser
        self.playwright, self.browser, self.context, self.page = setup_browser(headless)

    def login_manually(self, portal_url=None):
        """Login to VTU portal."""
        if not portal_url:
            portal_url = os.getenv("PORTAL_LOGIN_URL", "https://vtu.internyet.in/sign-in")

        login(self.page, self.context, portal_url, self.SESSION_DIR, self.profile_name)

    def fill_diary(self, data, dry_run=True):
        """Fill diary form."""
        return fill_diary(self.page, data, dry_run)

    def close(self):
        """Clean up browser resources."""
        if self.playwright and self.browser:
            close_browser(self.playwright, self.browser)
