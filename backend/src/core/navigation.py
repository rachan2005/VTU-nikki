import time
from datetime import datetime
from typing import Optional, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from .utils import handle_popups

def ensure_on_diary_page(driver, data: Optional[Dict] = None, wait_for_user=True):
    target_url = "https://vtu.internyet.in/dashboard/student/student-diary"
    
    if target_url in driver.current_url:
         if is_selection_page(driver):
             handle_selection_page(driver, data, wait_for_user)
         return

    try:
        handle_popups(driver)
        driver.get(target_url)
        time.sleep(4)
        handle_popups(driver)
        
        if is_selection_page(driver):
            handle_selection_page(driver, data, wait_for_user)
            
    except Exception as e:
        print(f"[VTU] Navigation failed: {e}")

def is_selection_page(driver):
    return len(driver.find_elements(By.NAME, "internship_id")) > 0

def handle_selection_page(driver, data: Optional[Dict] = None, wait_for_user=True):
    print("[VTU] Filling selection form...")
    wait = WebDriverWait(driver, 10)
    
    # 1. Select Internship
    try:
        # Try finding the internship select button/input
        intern_btn = None
        for selector in [(By.ID, "internship_id"), (By.NAME, "internship_id")]:
            try:
                intern_btn = driver.find_element(*selector)
                break
            except:
                continue
        
        if intern_btn:
            intern_btn.click()
            time.sleep(1)
            
            # Select first available option
            options = driver.find_elements(By.XPATH, "//div[@role='option'] | //*[contains(@class, 'select-item')]")
            if options:
                options[0].click()
            else:
                # Fallback JS
                driver.execute_script("document.getElementsByName('internship_id')[0].selectedIndex = 1;")
                driver.execute_script("document.getElementsByName('internship_id')[0].dispatchEvent(new Event('change'));")
    except Exception as e:
        print(f"[VTU] Internship select warning: {e}")
        try:
            driver.execute_script("document.getElementsByName('internship_id')[0].selectedIndex = 1;")
        except:
            pass
    
    # 2. Select Date
    target_date = data.get("date") if data else None
    day = str(datetime.now().day)
    
    if target_date:
        try:
            day = str(int(target_date.split('-')[2]))
        except:
            pass

    try:
        # Open calendar
        date_btn_found = False
        date_btn_selectors = [
            (By.XPATH, "//button[contains(., 'Pick a Date')]"),
            (By.XPATH, "//button[contains(., 'Date')]"),
            (By.CSS_SELECTOR, "button[aria-label*='date']"),
            (By.XPATH, "//input[@placeholder='Pick a Date']/following-sibling::button")
        ]

        for by, sel in date_btn_selectors:
            try:
                date_btn = driver.find_element(by, sel)
                if date_btn.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_btn)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", date_btn)
                    date_btn_found = True
                    print(f"[VTU] Opened date picker")
                    break
            except:
                continue

        if not date_btn_found:
            print("[VTU] Could not find date picker button")
            raise Exception("Date picker button not found")

        time.sleep(2)  # Wait longer for calendar popup

        # Pick Day - Try multiple strategies
        day_found = False

        # Strategy 1: Find by exact text match in visible elements
        day_selectors = [
            (By.XPATH, f"//button[normalize-space(text())='{day}' and not(@disabled)]"),
            (By.XPATH, f"//button[text()='{day}' and not(@disabled)]"),
            (By.XPATH, f"//div[@role='button' and normalize-space(text())='{day}']"),
            (By.XPATH, f"//td[@role='gridcell']//button[text()='{day}']"),
            (By.XPATH, f"//div[contains(@class, 'calendar')]//button[text()='{day}']"),
            (By.XPATH, f"//button[contains(@class, 'day') and text()='{day}']"),
            (By.CSS_SELECTOR, f"button:not([disabled])"),  # Fallback: find all enabled buttons
        ]

        for by, sel in day_selectors:
            try:
                elements = driver.find_elements(by, sel)
                for el in elements:
                    try:
                        # Check if element text matches day
                        if el.is_displayed() and el.is_enabled():
                            elem_text = el.text.strip()
                            if elem_text == day or elem_text == str(int(day)):
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                                time.sleep(0.3)
                                driver.execute_script("arguments[0].click();", el)
                                day_found = True
                                print(f"[VTU] Selected day {day}")
                                time.sleep(1)
                                break
                    except:
                        continue
                if day_found:
                    break
            except:
                continue

        if not day_found:
            print(f"[VTU] ⚠ Could not auto-select day {day}. Proceeding to Continue button...")

    except Exception as e:
        print(f"[VTU] Date selection warning: {e}")
        
    # 3. Click Continue Button
    if not wait_for_user:
        try:
            # Try multiple selectors for Continue button
            continue_selectors = [
                (By.XPATH, "//button[@type='submit' and contains(., 'Continue')]"),
                (By.XPATH, "//button[contains(text(), 'Continue')]"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[@type='submit']")
            ]

            btn_found = False
            for by, selector in continue_selectors:
                try:
                    btns = driver.find_elements(by, selector)
                    for btn in btns:
                        if btn.is_displayed():
                            # Scroll into view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(0.5)

                            # Remove disabled attribute
                            driver.execute_script("arguments[0].removeAttribute('disabled');", btn)
                            driver.execute_script("arguments[0].disabled = false;", btn)

                            # Click
                            driver.execute_script("arguments[0].click();", btn)
                            print(f"[VTU] Clicked Continue button")
                            btn_found = True

                            # Wait for page to load
                            time.sleep(3)
                            break
                    if btn_found:
                        break
                except:
                    continue

            if not btn_found:
                print("[VTU] ⚠ Continue button not found, proceeding anyway...")

        except Exception as e:
            print(f"[VTU] Continue button click failed: {e}")
