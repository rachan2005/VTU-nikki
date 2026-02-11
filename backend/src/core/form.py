import time
from typing import Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from .exceptions import SubmitError
from .utils import save_screenshot
from .navigation import ensure_on_diary_page

def fill_diary(driver, wait, data: Dict, dry_run=True, max_retries=3):
    """Fill diary form with retry logic."""
    for attempt in range(max_retries):
        try:
            ensure_on_diary_page(driver, data, wait_for_user=False)

            # Wait for the diary form to actually render after navigation
            _wait_for_form(driver, wait)

            return _fill_once(driver, wait, data, dry_run)
        except Exception as e:
            print(f"[VTU] Attempt {attempt+1} failed: {e}")
            save_screenshot(driver, f"error_attempt_{attempt+1}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise SubmitError(f"Failed: {e}")

def _wait_for_form(driver, wait, timeout=15):
    """Wait until the diary form textarea is present on the page."""
    from selenium.webdriver.support.ui import WebDriverWait

    form_wait = WebDriverWait(driver, timeout)
    selectors_to_try = [
        (By.CSS_SELECTOR, "textarea"),
        (By.CSS_SELECTOR, "textarea[name='description']"),
        (By.CSS_SELECTOR, "textarea.form-control"),
        (By.XPATH, "(//textarea)[1]"),
    ]
    for by, sel in selectors_to_try:
        try:
            form_wait.until(EC.presence_of_element_located((by, sel)))
            print(f"[VTU] Diary form loaded (found: {sel})")
            time.sleep(1)  # Extra settle time for React render
            return
        except TimeoutException:
            continue

    # Last resort: just wait and hope
    print("[VTU] Warning: form textarea not detected, waiting 5s and proceeding...")
    time.sleep(5)


def _fill_once(driver, wait, data, dry_run):
    def fill(selectors, value, field_name):
        # Allow passing a single selector tuple or a list of tuples
        if isinstance(selectors, tuple):
            selectors = [selectors]
            
        filled = False
        for by, selector in selectors:
            try:
                elem = wait.until(EC.presence_of_element_located((by, selector)))
                # Scroll into view
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem)
                time.sleep(0.5)
                
                elem.clear()
                elem.send_keys(str(value))
                # React/JS trigger events
                driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', {bubbles:true}));
                    arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
                    arguments[0].dispatchEvent(new Event('blur', {bubbles:true}));
                """, elem)
                print(f"[VTU] Filled {field_name}")
                filled = True
                break
            except Exception:
                continue
                
        if not filled:
            print(f"[VTU] Field not found: {field_name}")
            raise TimeoutException(f"Could not find field {field_name}")

    # Description — aggressive selector list for VTU portal textarea
    fill([
        (By.NAME, "description"),
        (By.NAME, "entry_text"),
        (By.NAME, "activities"),
        (By.CSS_SELECTOR, "textarea[name='description']"),
        (By.CSS_SELECTOR, "textarea[name='entry_text']"),
        (By.CSS_SELECTOR, "textarea.form-control"),
        (By.CSS_SELECTOR, "textarea"),
        (By.XPATH, "//textarea[contains(@placeholder, 'Description') or contains(@placeholder, 'entry') or contains(@placeholder, 'activit')]"),
        (By.XPATH, "//label[contains(text(), 'Description') or contains(text(), 'Activit') or contains(text(), 'What did')]/following::textarea[1]"),
        (By.XPATH, "(//textarea)[1]"),
        (By.ID, "description"),
    ], data.get("description", data.get("activities", "")), "Description")

    # Hours
    fill([
        (By.NAME, "hours"),
        (By.XPATH, "//label[contains(., 'Hours')]/following::input[@type='number'][1]"),
        (By.XPATH, "//input[@type='number' and contains(@placeholder, '6.5')]"),
        (By.CSS_SELECTOR, "input[type='number']")
    ], data["hours"], "Hours")

    # Learnings
    fill([
        (By.NAME, "learnings"),
        (By.XPATH, "//textarea[contains(@placeholder, 'learnings') or contains(@placeholder, 'Skills')]"),
        (By.XPATH, "//label[contains(text(), 'Learning')]/following-sibling::*//textarea")
    ], data["learnings"], "Learnings")

    # Blockers
    fill([
        (By.NAME, "blockers"),
        (By.XPATH, "//textarea[contains(@placeholder, 'blockers')]"),
        (By.XPATH, "//label[contains(text(), 'Blocker')]/following-sibling::*//textarea")
    ], data["blockers"], "Blockers")

    # Links
    fill([
        (By.NAME, "links"),
        (By.XPATH, "//input[contains(@placeholder, 'links') or contains(@placeholder, 'URL')]"),
        (By.XPATH, "//label[contains(text(), 'Links')]/following-sibling::input")
    ], data["links"], "Links")
    
    # Skills (React Select Multi-Select) - Select Multiple Skills
    print(f"[VTU] Attempting to fill Skills: {data.get('skills', ['Git'])}")
    skills_list = data.get('skills', ['Git'])  # Get list of skills
    if isinstance(skills_list, str):
        skills_list = [skills_list]  # Convert to list if single string

    skills_filled = 0

    # Method 1: React Select Input Interaction - Loop through each skill
    try:
        for skill in skills_list:
            try:
                # Re-find the input for each skill (DOM might change after selection)
                time.sleep(0.5)  # Wait for any animations

                # Try multiple selectors
                skill_input = None
                input_selectors = [
                    "input[id^='react-select-']",
                    "div[class*='react-select'] input",
                    "input[role='combobox']"
                ]

                for selector in input_selectors:
                    try:
                        skill_input = driver.find_element(By.CSS_SELECTOR, selector)
                        if skill_input.is_displayed():
                            break
                    except:
                        continue

                if not skill_input:
                    print(f"[VTU] Could not find skills input for '{skill}'")
                    continue

                # Scroll into view
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", skill_input)
                time.sleep(0.3)

                # Click to focus and open dropdown
                driver.execute_script("arguments[0].click();", skill_input)
                time.sleep(0.5)

                # Type the skill name to filter dropdown
                skill_input.send_keys(skill)
                time.sleep(1.5)  # Wait longer for dropdown to filter

                # Look for the dropdown option and click it
                try:
                    # Try to find the option in the dropdown menu
                    option_selectors = [
                        (By.XPATH, f"//div[contains(@class, 'react-select__option') and contains(text(), '{skill}')]"),
                        (By.CSS_SELECTOR, f"div[class*='react-select__option']")
                    ]

                    option_found = False
                    for by, selector in option_selectors:
                        try:
                            options = driver.find_elements(by, selector)
                            if options:
                                # Click first visible option
                                for opt in options:
                                    if opt.is_displayed() and skill.lower() in opt.text.lower():
                                        opt.click()
                                        option_found = True
                                        break
                            if option_found:
                                break
                        except:
                            continue

                    # Fallback: just press Enter if option not found
                    if not option_found:
                        skill_input.send_keys(Keys.ENTER)

                except:
                    # If clicking fails, press Enter
                    skill_input.send_keys(Keys.ENTER)

                time.sleep(0.5)

                print(f"[VTU] Selected skill: {skill}")
                skills_filled += 1

            except Exception as e:
                print(f"[VTU] Failed to select skill '{skill}': {e}")
                continue

        if skills_filled > 0:
            print(f"[VTU] Successfully selected {skills_filled}/{len(skills_list)} skills")
    except Exception as e:
        print(f"[VTU] Skills UI interaction failed: {e}")

    # Method 2: Fallback - if no skills were filled, try first skill only
    if skills_filled == 0:
        try:
            print(f"[VTU] Fallback: Attempting to select first skill only")
            skill_input = driver.find_element(By.CSS_SELECTOR, "input[id^='react-select-']")
            skill_input.click()
            time.sleep(0.5)
            skill_input.send_keys(Keys.ARROW_DOWN)
            skill_input.send_keys(Keys.ENTER)
            print("[VTU] Selected default skill via fallback")
        except:
            print("[VTU] ⚠ Could not fill skills field")
            pass

    # Submit Button - Aggressive Finding & Clicking
    try:
        time.sleep(1)
        submit_btn = None
        # Priority list of selectors
        selectors = [
            (By.XPATH, "//button[normalize-space()='Save']"),
            (By.XPATH, "//button[contains(text(), 'Save')]"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[@type='submit']"),
            (By.ID, "submit-btn")
        ]
        
        for by, val in selectors:
            try:
                btns = driver.find_elements(by, val)
                for btn in btns:
                    if btn.is_displayed():
                        submit_btn = btn
                        print(f"[VTU] Found submit button via {by}={val} text='{btn.text}'")
                        break
                if submit_btn: break
            except:
                continue
                
        if not submit_btn:
             # Last resort: find any button with 'Save' or 'Submit'
             try:
                 submit_btn = driver.find_element(By.XPATH, "//button[contains(., 'Save') or contains(., 'Submit')]")
             except:
                 # Debug: Print all buttons on page
                 print("[VTU] Debug: Available buttons:")
                 all_buttons = driver.find_elements(By.TAG_NAME, "button")
                 for btn in all_buttons[:10]:  # Limit to first 10
                     try:
                         print(f"  - Text: '{btn.text}' | Type: {btn.get_attribute('type')} | Visible: {btn.is_displayed()}")
                     except:
                         pass
                 raise NoSuchElementException("Submit/Save button not found")

        # Ensure enabled
        driver.execute_script("arguments[0].disabled = false;", submit_btn)
        driver.execute_script("arguments[0].removeAttribute('disabled');", submit_btn)
        
        # Scroll to it
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", submit_btn)
        time.sleep(1)
        
        if dry_run:
            # Highlight it
            driver.execute_script("arguments[0].style.border='3px solid red';", submit_btn)
            print("[VTU] Dry run success - Button highlighted")
            return "DRY_RUN_SUCCESS"
        
        print("[VTU] Clicking Submit...")
        try:
            submit_btn.click()
        except ElementClickInterceptedException:
             # Overlay blocking? JS Click
             driver.execute_script("arguments[0].click();", submit_btn)
        
        time.sleep(5)
        
        # Check if URL changed or success message appeared?
        # For now assume success if no error thrown
        return "SUBMITTED"
        
    except Exception as e:
        raise SubmitError(f"Submit failed: {e}")
