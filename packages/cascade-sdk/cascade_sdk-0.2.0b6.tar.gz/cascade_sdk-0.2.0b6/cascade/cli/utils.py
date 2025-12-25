"""
Utility functions for CLI process management
"""
import os
import sys
import json
import signal
import subprocess
import socket
from pathlib import Path
from typing import Optional, Dict, Tuple

# PID file location
CASCADE_DATA_DIR = Path.home() / ".cascade"
PID_FILE = CASCADE_DATA_DIR / "cascade.pid"


def ensure_data_dir():
    """Ensure cascade data directory exists."""
    CASCADE_DATA_DIR.mkdir(parents=True, exist_ok=True)


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except OSError:
            return True


def save_pids(otlp_pid: int, api_pid: int):
    """Save process IDs to file."""
    ensure_data_dir()
    pid_data = {
        "otlp_pid": otlp_pid,
        "api_pid": api_pid
    }
    with open(PID_FILE, 'w') as f:
        json.dump(pid_data, f)


def load_pids() -> Optional[Dict[str, int]]:
    """Load process IDs from file."""
    if not PID_FILE.exists():
        return None
    try:
        with open(PID_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def delete_pid_file():
    """Delete PID file."""
    if PID_FILE.exists():
        PID_FILE.unlink()


def is_process_running(pid: int) -> bool:
    """Check if a process is still running."""
    try:
        os.kill(pid, 0)  # Signal 0 doesn't kill, just checks if process exists
        return True
    except OSError:
        return False


def kill_process(pid: int, graceful: bool = True):
    """Kill a process gracefully or forcefully."""
    try:
        if graceful:
            os.kill(pid, signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGKILL)
        return True
    except OSError:
        return False


def get_backend_module_path(module_name: str) -> str:
    """Get the path to a backend module for running as a module."""
    # Try to find backend module relative to cascade package
    try:
        import cascade
        cascade_path = Path(cascade.__file__).parent.parent
        backend_path = cascade_path / "backend" / f"{module_name}.py"
        
        if backend_path.exists():
            # Use module syntax if it's installed as a package
            return f"backend.{module_name}"
    except Exception:
        pass
    
    # Fallback: try current directory
    current_dir = Path.cwd()
    backend_path = current_dir / "backend" / f"{module_name}.py"
    if backend_path.exists():
        # Return absolute path for subprocess
        return str(backend_path)
    
    # Last resort: assume it's installed and use module syntax
    return f"backend.{module_name}"


def get_backend_script_path(module_name: str) -> list:
    """Get command to run backend module."""
    import sys
    python_exe = sys.executable
    module_path = get_backend_module_path(module_name)
    
    # If it's a file path, run it directly
    if module_path.endswith('.py'):
        return [python_exe, module_path]
    else:
        # If it's a module, use -m flag
        return [python_exe, "-m", module_path]

