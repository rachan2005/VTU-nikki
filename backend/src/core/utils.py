import time
from datetime import datetime
from pathlib import Path
from selenium.webdriver.common.by import By

SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

def save_screenshot(driver, name: str = None):
    """Save screenshot with timestamp."""
    if not name:
        name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    filepath = SCREENSHOT_DIR / f"{name}.png"
    driver.save_screenshot(str(filepath))
    return filepath

def handle_popups(driver):
    """Detect and dismiss common VTU portal popups/modals."""
    print("[VTU] Checking for popups...")
    popup_selectors = [
        (By.XPATH, "//button[contains(text(), 'I Understand')]"),
        (By.XPATH, "//button[contains(text(), 'Close')]"),
        (By.XPATH, "//button[contains(text(), 'Dismiss')]"),
        (By.CSS_SELECTOR, ".modal-footer button"),
        (By.CSS_SELECTOR, "button.close-modal")
    ]
    
    # Short wait for popups to appear
    time.sleep(1)
    
    for by, selector in popup_selectors:
        try:
            # Find all matching elements
            elements = driver.find_elements(by, selector)
            for element in elements:
                if element.is_displayed():
                    print(f"[VTU] Found popup button: '{element.text}' - Dismissing...")
                    # Try regular click, then JavaScript click if blocked
                    try:
                        element.click()
                    except:
                        driver.execute_script("arguments[0].click();", element)
                    time.sleep(1) # Wait for animation
        except Exception:
            continue
