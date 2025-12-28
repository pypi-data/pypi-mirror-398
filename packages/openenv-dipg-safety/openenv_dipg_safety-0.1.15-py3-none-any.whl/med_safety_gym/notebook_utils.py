import subprocess
import time
import requests
import sys
import shutil

def run_bg_server(dataset_path=None, port=8000, timeout=60):
    """
    Starts the dipg-server in the background.
    
    This is useful for Kaggle/Colab notebooks where you want to run the server
    and then proceed to run evaluation cells in the same session.
    
    Args:
        dataset_path: Path to the dataset (local or HF). Defaults to env var or library default.
        port: The port to run on. Defaults to 8000.
        timeout: How many seconds to wait for the server to become healthy.
        
    Returns:
        The subprocess.Popen object representing the running server.
    """
    cmd = ["dipg-server", "--port", str(port)]
    if dataset_path:
        cmd.extend(["--dataset_path", dataset_path])
    
    # Check if we should use 'uv run' (common in this project's setup)
    # But for a general user who did 'pip install', 'dipg-server' is enough.
    # However, if they are in a dev environment with uv, uv run might be needed.
    # We'll try the direct command first, but allow fallbacks.
    
    print(f"--- Starting DIPG Server on port {port} ---")
    
    # In some environments, dipg-server might not be in the PATH yet if just installed.
    # We can use sys.executable -m med_safety_gym.app as a fallback
    
    # Try to find if 'dipg-server' exists in path
    if not shutil.which("dipg-server"):
        print("Note: 'dipg-server' command not found in PATH, using python module fallback.")
        cmd = [sys.executable, "-m", "med_safety_gym.app", "--port", str(port)]
        if dataset_path:
            cmd.extend(["--dataset_path", dataset_path])

    # Redirect output to a log file so it doesn't block the notebook pipe
    log_file = "dipg_server.log"
    
    popen_kwargs = {
        "stdout": None, # Will be set below
        "stderr": subprocess.STDOUT,
        "text": True,
    }
    
    if sys.platform != "win32":
        popen_kwargs["start_new_session"] = True
    else:
        # On Windows, use CREATE_NEW_PROCESS_GROUP to detach the process
        # This constant is specifically for Windows
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    with open(log_file, "w") as f:
        popen_kwargs["stdout"] = f
        process = subprocess.Popen(cmd, **popen_kwargs)
    
    # Wait for health check
    start_time = time.time()
    url = f"http://localhost:{port}/health"
    print(f"Waiting for server to become healthy at {url}...")
    
    is_healthy = False
    while time.time() - start_time < timeout:
        if process.poll() is not None:
            print("❌ Server process exited unexpectedly. Check dipg_server.log.")
            break
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                is_healthy = True
                print("✅ Server is healthy and running in the background!")
                break
        except requests.exceptions.RequestException:
            time.sleep(2)
            
    if not is_healthy:
        process.terminate()
        raise RuntimeError(f"Server failed to start within {timeout}s. See dipg_server.log for details.")
        
    return process

def stop_bg_server(process):
    """Safely terminates a background server process."""
    if process:
        print("Stopping DIPG Server...")
        process.terminate()
        try:
            process.wait(timeout=10)
            print("✅ Server stopped.")
        except subprocess.TimeoutExpired:
            print("Server didn't stop, killing...")
            process.kill()
            print("✅ Server killed.")
