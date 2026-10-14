"""Runner script to launch the Kisan Shakti Streamlit frontend."""
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    app_path = PROJECT_ROOT / "frontend" / "app.py"
    print(f"Launching Kisan Shakti Web GUI from {app_path} ...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port=8501", "--server.headless=true"])
