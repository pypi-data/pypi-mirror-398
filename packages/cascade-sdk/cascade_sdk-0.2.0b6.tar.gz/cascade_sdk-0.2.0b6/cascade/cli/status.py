"""
Status command for Cascade CLI
Checks status of backend services
"""
import socket
from pathlib import Path
from cascade.cli.utils import load_pids, is_process_running, is_port_in_use, CASCADE_DATA_DIR


def check_status():
    """
    Check status of Cascade services.
    
    Returns:
        Dict with status information
    """
    pids = load_pids()
    
    status = {
        "otlp_running": False,
        "api_running": False,
        "otlp_pid": None,
        "api_pid": None,
        "otlp_port": 4317,
        "api_port": 8000,
        "data_dir": str(CASCADE_DATA_DIR),
    }
    
    # Check OTLP receiver
    if pids:
        otlp_pid = pids.get("otlp_pid")
        api_pid = pids.get("api_pid")
        
        status["otlp_pid"] = otlp_pid
        status["api_pid"] = api_pid
        
        if otlp_pid and is_process_running(otlp_pid):
            status["otlp_running"] = True
        
        if api_pid and is_process_running(api_pid):
            status["api_running"] = True
    
    # Also check ports as backup
    if is_port_in_use(status["otlp_port"]):
        status["otlp_running"] = True
    
    if is_port_in_use(status["api_port"]):
        status["api_running"] = True
    
    # Check if API is responding
    status["api_responding"] = False
    if status["api_running"]:
        try:
            import urllib.request
            response = urllib.request.urlopen(f"http://localhost:{status['api_port']}/health", timeout=1)
            if response.getcode() == 200:
                status["api_responding"] = True
        except Exception:
            pass
    
    return status


def print_status():
    """Print status information to console."""
    status = check_status()
    
    print("Cascade Services Status")
    print("=" * 50)
    
    # OTLP Receiver
    otlp_status = "✓ Running" if status["otlp_running"] else "✗ Stopped"
    print(f"OTLP Receiver: {otlp_status}")
    if status["otlp_pid"]:
        print(f"  PID: {status['otlp_pid']}")
    print(f"  Port: {status['otlp_port']}")
    print(f"  Endpoint: http://localhost:{status['otlp_port']}")
    
    print()
    
    # REST API
    api_status = "✓ Running" if status["api_running"] else "✗ Stopped"
    print(f"REST API: {api_status}")
    if status["api_pid"]:
        print(f"  PID: {status['api_pid']}")
    print(f"  Port: {status['api_port']}")
    print(f"  URL: http://localhost:{status['api_port']}")
    
    if status["api_responding"]:
        print("  Health: ✓ Responding")
    elif status["api_running"]:
        print("  Health: ⚠️  Not responding")
    
    print()
    
    # Data directory
    print(f"Data Directory: {status['data_dir']}")
    db_path = Path(status['data_dir']) / "data" / "traces.db"
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"  Database: {db_path} ({size_mb:.2f} MB)")
    else:
        print(f"  Database: Not created yet")
    
    print()
    
    # Overall status
    if status["otlp_running"] and status["api_running"]:
        print("✅ All services are running")
        print(f"\n   View traces: curl http://localhost:{status['api_port']}/api/traces")
    elif status["otlp_running"] or status["api_running"]:
        print("⚠️  Some services are running")
        print("   Run 'cascade stop' and 'cascade start' to restart")
    else:
        print("✗ Services are not running")
        print("   Run 'cascade start' to start services")

