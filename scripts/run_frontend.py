"""Runner script to launch the Kisan Shakti Streamlit frontend."""
import os
import sys
import socket
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def find_available_port(start_port=8501, max_tries=10):
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port

if __name__ == "__main__":
    app_path = PROJECT_ROOT / "frontend" / "app.py"
    port = find_available_port(8501)
    print(f"Launching Kisan Shakti Web GUI on http://localhost:{port} ...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(app_path),
        f"--server.port={port}",
        "--server.headless=false"
    ])
