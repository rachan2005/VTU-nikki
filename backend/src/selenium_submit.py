from pathlib import Path
from src.core.driver import setup_driver
from src.core.exceptions import SubmitError
from src.core.session import save_session, load_session
from src.core.auth import login, manual_login_prompt
from src.core.form import fill_diary

class VTUSubmitter:
    """Facade for VTU automation."""
    
    SESSION_DIR = Path("sessions")

    def __init__(self, headless=False, profile_name="default", wait_for_user=True):
        self.headless = headless
        self.profile_name = profile_name
        self.wait_for_user = wait_for_user
        
        self.SESSION_DIR.mkdir(exist_ok=True)
        self.driver, self.wait = setup_driver(headless, profile_name, self.SESSION_DIR)

    def login_manually(self, portal_url=None):
        login(self.driver, self.wait, portal_url, self.SESSION_DIR, self.profile_name, self.wait_for_user)

    def fill_diary(self, data, dry_run=True):
        return fill_diary(self.driver, self.wait, data, dry_run)
    
    def close(self):
        if self.driver:
            self.driver.quit()
