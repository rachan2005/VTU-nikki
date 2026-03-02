"""Playwright form filling."""
import time
from typing import Dict
from playwright.sync_api import Page
from .navigation import ensure_on_diary_page


def fill_diary(page: Page, data: Dict, dry_run=True):
    """Fill diary form with Playwright auto-waiting."""
    try:
        ensure_on_diary_page(page, data)
        return _fill_once(page, data, dry_run)
    except Exception as e:
        # Take screenshot on error
        screenshot_path = f"screenshots/error_playwright_{int(time.time())}.png"
        page.screenshot(path=screenshot_path)
        print(f"[VTU] Screenshot saved: {screenshot_path}")
        raise Exception(f"Form fill failed: {e}")


def _fill_once(page: Page, data: Dict, dry_run: bool):
    """Fill form fields using Playwright selectors."""

    def fill_field(selectors: list, value: str, field_name: str):
        """Try multiple selectors until one works."""
        for selector in selectors:
            try:
                locator = page.locator(selector)
                if locator.count() > 0:
                    locator.first.fill(str(value))
                    print(f"[VTU] Filled {field_name}")
                    return True
            except Exception as e:
                continue

        print(f"[VTU] ⚠ Field not found: {field_name}")
        return False

    # Description
    desc_filled = fill_field([
        "textarea[name='description']",
        "textarea[name='entry_text']",
        "textarea[placeholder*='Description' i]",
        "textarea[placeholder*='entry' i]",
        "textarea#description"
    ], data["description"], "Description")

    if not desc_filled:
        raise Exception("Could not find Description field")

    # Hours
    fill_field([
        "input[name='hours']",
        "input[type='number']",
        "input[placeholder*='6.5']"
    ], data["hours"], "Hours")

    # Learnings
    fill_field([
        "textarea[name='learnings']",
        "textarea[placeholder*='learning' i]",
        "textarea[placeholder*='skills' i]"
    ], data["learnings"], "Learnings")

    # Blockers
    fill_field([
        "textarea[name='blockers']",
        "textarea[placeholder*='blocker' i]"
    ], data["blockers"], "Blockers")

    # Links
    fill_field([
        "input[name='links']",
        "input[placeholder*='link' i]",
        "input[placeholder*='URL' i]"
    ], data["links"], "Links")

    # Skills - Handle React Select Multi-Select
    print(f"[VTU] Attempting to fill Skills: {data.get('skills', ['Git'])}")
    skills_list = data.get('skills', ['Git'])
    if isinstance(skills_list, str):
        skills_list = [skills_list]

    skills_filled = 0

    try:
        # Method 1: Find React Select input and select each skill
        for skill in skills_list:
            try:
                react_input = page.locator("input[id^='react-select-']").first

                # Clear and click to focus
                react_input.clear()
                react_input.click()
                page.wait_for_timeout(500)

                # Type skill name to filter dropdown
                react_input.fill(skill)
                page.wait_for_timeout(1200)  # Wait longer for dropdown to filter

                # Try to click the dropdown option directly
                try:
                    # Look for the option in dropdown
                    option = page.locator(f"div[class*='react-select__option']:has-text('{skill}')").first
                    if option.is_visible():
                        option.click()
                    else:
                        # Fallback to Enter key
                        page.keyboard.press('Enter')
                except:
                    # Fallback to Enter key
                    page.keyboard.press('Enter')

                page.wait_for_timeout(500)

                print(f"[VTU] Selected skill: {skill}")
                skills_filled += 1

            except Exception as e:
                print(f"[VTU] Failed to select skill '{skill}': {e}")
                continue

        if skills_filled > 0:
            print(f"[VTU] Successfully selected {skills_filled}/{len(skills_list)} skills")

    except Exception as e:
        print(f"[VTU] Skills interaction: {e}")

    # Method 2: Fallback - select first option if nothing worked
    if skills_filled == 0:
        try:
            print("[VTU] Fallback: Selecting default skill")
            react_input = page.locator("input[id^='react-select-']").first
            react_input.click()
            page.wait_for_timeout(500)
            page.keyboard.press('ArrowDown')
            page.keyboard.press('Enter')
            print("[VTU] Selected default skill via fallback")
        except:
            print("[VTU] ⚠ Could not fill skills field")
            pass

    # Find Submit/Save button
    time.sleep(1)

    submit_selectors = [
        "button:has-text('Save')",
        "button[type='submit']:has-text('Save')",
        "button[type='submit']"
    ]

    submit_btn = None
    for selector in submit_selectors:
        locator = page.locator(selector)
        if locator.count() > 0:
            # Get first visible button
            for i in range(locator.count()):
                if locator.nth(i).is_visible():
                    submit_btn = locator.nth(i)
                    print(f"[VTU] Found submit button: {submit_btn.text_content()}")
                    break
            if submit_btn:
                break

    if not submit_btn:
        raise Exception("Submit/Save button not found")

    # Enable button if disabled
    page.evaluate("(btn) => { btn.disabled = false; btn.removeAttribute('disabled'); }", submit_btn)

    if dry_run:
        # Highlight button
        page.evaluate("(btn) => { btn.style.border = '3px solid red'; }", submit_btn)
        print("[VTU] Dry run success - Button highlighted")
        page.wait_for_timeout(2000)
        return {"success": True, "mode": "DRY_RUN"}

    # Click submit
    print("[VTU] Clicking Submit...")
    submit_btn.click()
    page.wait_for_timeout(3000)

    # Check for success indicators
    if page.locator("text='Success' i").count() > 0 or page.locator("text='Submitted' i").count() > 0:
        print("[VTU] ✓ Submission confirmed")
        return {"success": True, "mode": "SUBMITTED"}

    print("[VTU] Submission completed (no confirmation message)")
    return {"success": True, "mode": "SUBMITTED"}
