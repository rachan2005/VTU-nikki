import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from .session import load_session, save_session
from .utils import handle_popups

def manual_login_prompt(driver, wait_for_user=True, session_dir=None, profile_name="default"):
    """Prompt user to login manually."""
    print("\n[VTU] Please login manually and navigate to diary page.")
    if wait_for_user:
        input("Press ENTER when ready...")
    else:
        # Increased wait for manual login in web/headless mode
        print("[VTU] Waiting 60s for manual login...")
        time.sleep(60)
    
    try:
        handle_popups(driver)
        if session_dir:
            save_session(driver, session_dir, profile_name)
    except Exception as e:
        print(f"[VTU] ⚠ Could not save session: {e}")

def login(driver, wait, portal_url=None, session_dir=None, profile_name="default", wait_for_user=True):
    """Open portal and attempt automatic login."""
    if not portal_url:
        portal_url = os.getenv("PORTAL_LOGIN_URL", "https://vtu.internyet.in/sign-in")
    
    print(f"[VTU] Opening: {portal_url}")
    try:
        driver.get(portal_url)
    except WebDriverException:
        manual_login_prompt(driver, wait_for_user, session_dir, profile_name)
        return

    # Try Session
    if session_dir and load_session(driver, session_dir, profile_name):
        driver.refresh()
        time.sleep(2)
        try:
            # Check if logged in
            driver.find_element(By.XPATH, "//*[contains(text(), 'Logout') or contains(text(), 'Sign Out') or contains(text(), 'Dashboard')]")
            print("[VTU] Session valid")
            return
        except NoSuchElementException:
            print("[VTU] Session expired")
            pass
    
    email = os.getenv("VTU_EMAIL")
    password = os.getenv("VTU_PASSWORD")
    
    if not email or not password:
        manual_login_prompt(driver, wait_for_user, session_dir, profile_name)
        return

    print("[VTU] Attempting auto-login...")
    try:
        # Helper to find elements
        def find_any(selectors):
            for by, val in selectors:
                try:
                    return wait.until(EC.presence_of_element_located((by, val)))
                except:
                    continue
            return None

        # Extensive Email Selectors (restored from original working script)
        email_field = find_any([
            (By.CSS_SELECTOR, "input[autocomplete='email']"),
            (By.XPATH, "//input[@autocomplete='email']"),
            (By.XPATH, "//input[@placeholder='Enter your email address']"), 
            (By.ID, "email"),
            (By.NAME, "email"),
            (By.XPATH, "//input[@type='email']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "#email"),
            (By.XPATH, "//*[@name='email']")
        ])
        
        if not email_field:
            # Debugging aid
            print(f"[VTU] Debug: Current URL is {driver.current_url}")
            raise NoSuchElementException("Email field not found")
            
        email_field.clear()
        email_field.send_keys(email)
        
        # Extensive Password Selectors
        pass_field = find_any([
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.XPATH, "//input[@autocomplete='new-password']"),
            (By.XPATH, "//input[@autocomplete='current-password']"), 
            (By.XPATH, "//input[@placeholder='Enter your password']"),
            (By.CSS_SELECTOR, "input[type='password']")
        ])
        if not pass_field: raise NoSuchElementException("Password field not found")
        pass_field.clear()
        pass_field.send_keys(password)
        
        # Extensive Submit Selectors
        submit_btn = find_any([
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Sign In') or contains(text(), 'Login') or contains(text(), 'Submit')]"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.ID, "submit"),
            (By.ID, "login-button")
        ])
        if not submit_btn: raise NoSuchElementException("Submit button not found")
        
        driver.execute_script("arguments[0].click();", submit_btn)
        
        time.sleep(3)
        handle_popups(driver)
        
        # Verify login success
        try:
            error = driver.find_element(By.XPATH, "//*[contains(text(), 'Invalid') or contains(text(), 'failed')]")
            if error.is_displayed():
                 raise Exception(f"Login error displayed: {error.text}")
        except NoSuchElementException:
            pass
            
        if session_dir:
            save_session(driver, session_dir, profile_name)
        
        print("[VTU] Auto-login successful")
            
    except Exception as e:
        print(f"[VTU] Auto-login failed: {e}")
        manual_login_prompt(driver, wait_for_user, session_dir, profile_name)
