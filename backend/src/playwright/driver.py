"""Playwright browser driver setup."""
import os
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext


def setup_browser(headless=True):
    """Initialize Playwright browser with anti-detection measures."""
    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=headless,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage'
        ]
    )

    # Create context with realistic settings
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        locale='en-US',
        timezone_id='Asia/Kolkata'
    )

    # Anti-detection: Remove webdriver flag
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    page = context.new_page()
    page.set_default_timeout(30000)  # 30 second timeout

    return playwright, browser, context, page


def close_browser(playwright, browser):
    """Clean up browser resources."""
    if browser:
        browser.close()
    if playwright:
        playwright.stop()
