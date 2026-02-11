import os
import subprocess
import sys
import shutil
from pathlib import Path

def print_banner():
    print("=" * 60)
    print("   VTU Diary Automation - Project Setup")
    print("=" * 60)

def run_command(command, cwd=None, shell=True):
    """Run a shell command and return its exit code."""
    print(f"\n> Running: {' '.join(command) if isinstance(command, list) else command}")
    try:
        process = subprocess.run(command, cwd=cwd, shell=shell, check=True)
        return process.returncode
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed with exit code {e.returncode}")
        return e.returncode

def main():
    root_dir = Path(__file__).parent.absolute()
    backend_dir = root_dir / "backend"
    frontend_dir = root_dir / "frontend"
    venv_dir = root_dir / ".venv"

    print_banner()

    # 1. Virtual Environment
    print("\n[1/5] Setting up Python Virtual Environment...")
    if not venv_dir.exists():
        if run_command([sys.executable, "-m", "venv", str(venv_dir)]) != 0:
            print("Failed to create virtual environment.")
            return
        print("✓ Virtual environment created.")
    else:
        print("✓ Virtual environment already exists.")

    # Determine pip and python paths in venv
    if os.name == 'nt':  # Windows
        venv_python = venv_dir / "Scripts" / "python.exe"
        venv_pip = venv_dir / "Scripts" / "pip.exe"
    else:  # Unix
        venv_python = venv_dir / "bin" / "python"
        venv_pip = venv_dir / "bin" / "pip"

    # 2. Backend Dependencies
    print("\n[2/5] Installing Backend Dependencies...")
    run_command([str(venv_pip), "install", "--upgrade", "pip"])
    if run_command([str(venv_pip), "install", "-r", str(backend_dir / "requirements.txt")]) != 0:
        print("Failed to install backend requirements.")
        return
    
    print("Installing Playwright browsers...")
    run_command([str(venv_python), "-m", "playwright", "install", "chromium"])

    # 3. Environment Variables
    print("\n[3/5] Setting up Environment Variables...")
    env_file = root_dir / ".env"
    env_example = root_dir / ".env.example"
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("✓ Created .env from .env.example")
        else:
            print("! .env.example not found, skipping.")
    else:
        print("✓ .env already exists.")

    # 4. Frontend Dependencies
    print("\n[4/5] Installing Frontend Dependencies (requires Node.js)...")
    if shutil.which("npm"):
        if run_command("npm install", cwd=frontend_dir) != 0:
            print("Failed to install frontend dependencies.")
        else:
            print("✓ Frontend dependencies installed.")
    else:
        print("[WARNING] npm not found. Please install Node.js to use the frontend.")

    # 5. Build Frontend
    print("\n[5/5] Building Frontend...")
    if shutil.which("npm"):
        if run_command("npm run build", cwd=frontend_dir) != 0:
            print("Failed to build frontend.")
        else:
            print("✓ Frontend build complete.")
    
    print("\n" + "=" * 60)
    print("   Setup Complete! 🚀")
    print("=" * 60)
    print("\nTo run the application:")
    if os.name == 'nt':
        print(f"  1. Activate venv: .venv\\Scripts\\activate")
    else:
        print(f"  1. Activate venv: source .venv/bin/activate")
    print(f"  2. Start backend: cd backend && python app.py")
    print(f"  3. Open browser:  http://localhost:5000")
    print("\nNote: You can also use 'docker-compose up --build'")
    print("=" * 60)

if __name__ == "__main__":
    main()
