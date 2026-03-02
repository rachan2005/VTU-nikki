import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from .exceptions import SubmitError

DEFAULT_TIMEOUT = 20

def setup_driver(headless=False, profile_name="default", session_dir=Path("sessions")):
    """Setup Chrome driver with robust options."""
    options = Options()
    
    if headless:
        options.add_argument("--headless=new")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--remote-debugging-pipe")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User data dir for session persistence
    user_data_dir = session_dir / profile_name
    user_data_dir.mkdir(parents=True, exist_ok=True)
    options.add_argument(f"--user-data-dir={str(user_data_dir.absolute())}")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            wait = WebDriverWait(driver, DEFAULT_TIMEOUT)
            
            # Anti-detection
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            return driver, wait
            
        except Exception as e:
            print(f"[Driver] Init attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                raise SubmitError(f"Failed to initialize Chrome driver after {max_retries} attempts: {e}")
