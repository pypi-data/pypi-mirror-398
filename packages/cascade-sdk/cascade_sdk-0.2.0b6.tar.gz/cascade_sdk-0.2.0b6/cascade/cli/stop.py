"""
Stop command for Cascade CLI
Stops backend services
"""
import time
from cascade.cli.utils import load_pids, delete_pid_file, is_process_running, kill_process


def stop_services():
    """
    Stop backend services.
    
    Returns:
        True if services were stopped, False otherwise
    """
    pids = load_pids()
    
    if not pids:
        print("ℹ️  No running Cascade services found (no PID file).")
        print("   Services may have been stopped manually or never started.")
        return False
    
    otlp_pid = pids.get("otlp_pid")
    api_pid = pids.get("api_pid")
    
    stopped_any = False
    
    # Stop OTLP receiver
    if otlp_pid:
        if is_process_running(otlp_pid):
            print(f"Stopping OTLP receiver (PID: {otlp_pid})...")
            if kill_process(otlp_pid, graceful=True):
                # Wait for graceful shutdown
                for _ in range(10):  # Wait up to 1 second
                    if not is_process_running(otlp_pid):
                        break
                    time.sleep(0.1)
                
                if is_process_running(otlp_pid):
                    print("   Force killing OTLP receiver...")
                    kill_process(otlp_pid, graceful=False)
                
                print("✓ OTLP receiver stopped")
                stopped_any = True
            else:
                print("⚠️  Could not stop OTLP receiver (process may have already exited)")
        else:
            print(f"ℹ️  OTLP receiver (PID: {otlp_pid}) is not running")
    
    # Stop REST API
    if api_pid:
        if is_process_running(api_pid):
            print(f"Stopping REST API (PID: {api_pid})...")
            if kill_process(api_pid, graceful=True):
                # Wait for graceful shutdown
                for _ in range(10):  # Wait up to 1 second
                    if not is_process_running(api_pid):
                        break
                    time.sleep(0.1)
                
                if is_process_running(api_pid):
                    print("   Force killing REST API...")
                    kill_process(api_pid, graceful=False)
                
                print("✓ REST API stopped")
                stopped_any = True
            else:
                print("⚠️  Could not stop REST API (process may have already exited)")
        else:
            print(f"ℹ️  REST API (PID: {api_pid}) is not running")
    
    # Delete PID file
    delete_pid_file()
    
    if stopped_any:
        print("\n✅ Cascade services stopped")
    else:
        print("\nℹ️  No services were running")
    
    return stopped_any

