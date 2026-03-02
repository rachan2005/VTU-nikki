"""Playwright navigation and page interaction."""
import time
from datetime import datetime
from typing import Optional, Dict
from playwright.sync_api import Page


def handle_popups(page: Page):
    """Dismiss any modal popups."""
    try:
        # Look for common popup dismiss buttons
        dismiss_selectors = [
            "button:has-text('I Understand')",
            "button:has-text('OK')",
            "button:has-text('Close')",
            "[aria-label='Close']"
        ]

        for selector in dismiss_selectors:
            if page.locator(selector).count() > 0:
                page.click(selector, timeout=2000)
                print(f"[VTU] Dismissed popup")
                time.sleep(0.5)
    except:
        pass


def ensure_on_diary_page(page: Page, data: Optional[Dict] = None):
    """Navigate to diary page and handle selection if needed."""
    target_url = "https://vtu.internyet.in/dashboard/student/student-diary"

    if target_url not in page.url:
        handle_popups(page)
        page.goto(target_url)
        time.sleep(2)
        handle_popups(page)

    # Check if on selection page
    if page.locator("[name='internship_id']").count() > 0:
        handle_selection_page(page, data)


def handle_selection_page(page: Page, data: Optional[Dict] = None):
    """Fill internship and date selection form."""
    print("[VTU] Filling selection form...")

    # 1. Select Internship
    try:
        # Click internship dropdown
        page.click("[name='internship_id']", timeout=5000)
        time.sleep(1)

        # Select first available option
        options = page.locator("div[role='option'], *[class*='select-item']")
        if options.count() > 0:
            options.first.click()
            print("[VTU] Selected internship")
    except Exception as e:
        print(f"[VTU] Internship select warning: {e}")

    # 2. Select Date
    target_date = data.get("date") if data else None
    day = str(datetime.now().day)

    if target_date:
        try:
            day = str(int(target_date.split('-')[2]))
        except:
            pass

    try:
        # Click date picker button
        date_button_found = False
        date_selectors = [
            "button:has-text('Pick a Date')",
            "button:has-text('Date')",
            "button[aria-label*='date' i]"
        ]

        for selector in date_selectors:
            if page.locator(selector).count() > 0:
                page.click(selector)
                date_button_found = True
                print("[VTU] Opened date picker")
                break

        if not date_button_found:
            raise Exception("Date picker button not found")

        page.wait_for_timeout(1000)  # Wait for calendar to appear

        # Click the day - Playwright auto-waits and retries
        day_clicked = False
        day_selectors = [
            f"button:has-text('{day}'):not([disabled])",
            f"div[role='button']:has-text('{day}')",
            f"td[role='gridcell'] button:has-text('{day}')",
            f"*[class*='calendar'] button:has-text('{day}')"
        ]

        for selector in day_selectors:
            try:
                locator = page.locator(selector)
                if locator.count() > 0:
                    # Get visible element
                    locator.first.click(timeout=5000)
                    day_clicked = True
                    print(f"[VTU] Selected day {day}")
                    break
            except:
                continue

        if not day_clicked:
            print(f"[VTU] ⚠ Could not auto-select day {day}")

    except Exception as e:
        print(f"[VTU] Date selection warning: {e}")

    # 3. Click Continue
    try:
        continue_btn = page.locator("button[type='submit']:has-text('Continue')")
        if continue_btn.count() > 0:
            continue_btn.click()
            print("[VTU] Clicked Continue")
            page.wait_for_load_state("networkidle", timeout=10000)
    except Exception as e:
        print(f"[VTU] Continue button: {e}")
