import json
from pathlib import Path

def save_session(driver, session_dir: Path, profile_name: str):
    """Save cookies for session reuse."""
    cookies = driver.get_cookies()
    session_file = session_dir / f"{profile_name}_cookies.json"
    
    with open(session_file, "w") as f:
        json.dump(cookies, f, indent=2)
    
    return session_file

def load_session(driver, session_dir: Path, profile_name: str):
    """Load cookies from saved session."""
    session_file = session_dir / f"{profile_name}_cookies.json"
    
    if not session_file.exists():
        return False
    
    try:
        with open(session_file, "r") as f:
            cookies = json.load(f)
        
        for cookie in cookies:
            driver.add_cookie(cookie)
        
        return True
    except Exception as e:
        print(f"Failed to load session: {e}")
        return False
