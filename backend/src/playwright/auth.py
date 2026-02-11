"""Playwright authentication handling."""
import os
import json
from pathlib import Path
from playwright.sync_api import Page, BrowserContext
from .navigation import handle_popups


def save_session(context: BrowserContext, session_dir: Path, profile_name: str):
    """Save browser session cookies."""
    session_dir.mkdir(parents=True, exist_ok=True)
    session_file = session_dir / f"{profile_name}_cookies.json"

    cookies = context.cookies()
    with open(session_file, 'w') as f:
        json.dump(cookies, f)

    print(f"[VTU] Session saved to {session_file}")


def load_session(context: BrowserContext, session_dir: Path, profile_name: str):
    """Load browser session cookies."""
    session_file = session_dir / f"{profile_name}_cookies.json"

    if not session_file.exists():
        return False

    try:
        with open(session_file, 'r') as f:
            cookies = json.load(f)

        context.add_cookies(cookies)
        print(f"[VTU] Session loaded from {session_file}")
        return True
    except Exception as e:
        print(f"[VTU] Failed to load session: {e}")
        return False


def login(page: Page, context: BrowserContext, portal_url: str, session_dir: Path, profile_name: str):
    """Handle login to VTU portal."""
    print(f"[VTU] Opening: {portal_url}")
    page.goto(portal_url)
    handle_popups(page)

    # Try loading saved session
    if load_session(context, session_dir, profile_name):
        page.reload()
        page.wait_for_timeout(2000)
        handle_popups(page)

        # Check if logged in
        if "dashboard" in page.url or page.locator("text='Student Dashboard'").count() > 0:
            print("[VTU] Session valid - logged in")
            return

    # Auto-login with credentials
    print("[VTU] Attempting auto-login...")
    email = os.getenv("VTU_EMAIL")
    password = os.getenv("VTU_PASSWORD")

    if email and password:
        try:
            # Fill login form
            page.fill("input[type='email'], input[name='email']", email, timeout=5000)
            page.fill("input[type='password'], input[name='password']", password, timeout=5000)

            # Click login button
            login_selectors = [
                "button[type='submit']",
                "button:has-text('Sign In')",
                "button:has-text('Login')"
            ]

            for selector in login_selectors:
                if page.locator(selector).count() > 0:
                    page.click(selector)
                    break

            # Wait for navigation
            page.wait_for_load_state("networkidle", timeout=15000)
            handle_popups(page)

            # Check if login successful
            if "dashboard" in page.url or page.locator("text='Student Dashboard'").count() > 0:
                print("[VTU] Auto-login successful")
                save_session(context, session_dir, profile_name)
                return

        except Exception as e:
            print(f"[VTU] Auto-login failed: {e}")

    # Fallback: Wait for manual login
    print("[VTU] ⚠ Please log in manually...")
    print("[VTU] Waiting for dashboard page...")

    try:
        page.wait_for_url("**/dashboard/**", timeout=120000)
        handle_popups(page)
        save_session(context, session_dir, profile_name)
        print("[VTU] Manual login successful")
    except:
        raise Exception("Login timeout - dashboard page not reached")
