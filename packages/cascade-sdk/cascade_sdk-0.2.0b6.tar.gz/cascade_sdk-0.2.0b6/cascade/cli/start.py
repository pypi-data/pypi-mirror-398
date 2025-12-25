"""
Start command for Cascade CLI
Starts backend services (OTLP receiver and REST API)
"""
import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from cascade.cli.utils import (
    is_port_in_use, save_pids, get_backend_module_path, get_backend_script_path,
    ensure_data_dir, PID_FILE, is_process_running, kill_process
)

logger = logging.getLogger(__name__)


def start_services(otlp_port: int = 4317, api_port: int = 8000, background: bool = True):
    """
    Start backend services.
    
    Args:
        otlp_port: Port for OTLP gRPC receiver
        api_port: Port for REST API
        background: Whether to run in background
    
    Returns:
        Tuple of (otlp_pid, api_pid) or None if failed
    """
    # Check if services are already running
    if is_port_in_use(otlp_port):
        print(f"⚠️  Port {otlp_port} is already in use. OTLP receiver may already be running.")
        return None
    
    if is_port_in_use(api_port):
        print(f"⚠️  Port {api_port} is already in use. REST API may already be running.")
        return None
    
    # Ensure data directory exists
    ensure_data_dir()
    
    # Get commands to run backend modules
    otlp_cmd = get_backend_script_path("otel_receiver")
    
    # Prepare log files
    log_dir = Path.home() / ".cascade" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    otlp_log = log_dir / "otel_receiver.log"
    api_log = log_dir / "api.log"
    
    try:
        # Start OTLP receiver
        print(f"Starting OTLP receiver on port {otlp_port}...")
        otlp_process = subprocess.Popen(
            otlp_cmd,
            stdout=open(otlp_log, 'w'),
            stderr=subprocess.STDOUT,
            cwd=str(Path.cwd())
        )
        
        # Wait a moment for OTLP to start
        time.sleep(1)
        
        if not is_process_running(otlp_process.pid):
            print(f"❌ Failed to start OTLP receiver. Check logs: {otlp_log}")
            return None
        
        print(f"✓ OTLP receiver started (PID: {otlp_process.pid})")
        
        # Start REST API
        print(f"Starting REST API on port {api_port}...")
        # For FastAPI, we need to use uvicorn
        api_module = get_backend_module_path("main")
        if api_module.endswith('.py'):
            # If it's a file path, we need to adjust for uvicorn
            api_module = api_module.replace('.py', '').replace('/', '.').replace('\\', '.')
        
        api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", f"{api_module}:app", "--host", "0.0.0.0", "--port", str(api_port)],
            stdout=open(api_log, 'w'),
            stderr=subprocess.STDOUT,
            cwd=str(Path.cwd())
        )
        
        # Wait a moment for API to start
        time.sleep(2)
        
        if not is_process_running(api_process.pid):
            print(f"❌ Failed to start REST API. Check logs: {api_log}")
            # Try to kill OTLP if API failed
            kill_process(otlp_process.pid)
            return None
        
        print(f"✓ REST API started (PID: {api_process.pid})")
        
        # Save PIDs
        save_pids(otlp_process.pid, api_process.pid)
        
        # Verify services are responding
        import urllib.request
        try:
            time.sleep(1)
            response = urllib.request.urlopen(f"http://localhost:{api_port}/health", timeout=2)
            if response.getcode() == 200:
                print(f"\n✅ Cascade services are running!")
                print(f"   OTLP endpoint: http://localhost:{otlp_port}")
                print(f"   REST API: http://localhost:{api_port}")
                print(f"   Logs: {log_dir}")
                print(f"\n   View traces: curl http://localhost:{api_port}/api/traces")
                return (otlp_process.pid, api_process.pid)
        except Exception as e:
            print(f"⚠️  Services started but health check failed: {e}")
            print(f"   Check logs: {log_dir}")
            return (otlp_process.pid, api_process.pid)
        
    except Exception as e:
        logger.error(f"Error starting services: {e}", exc_info=True)
        print(f"❌ Error starting services: {e}")
        return None



