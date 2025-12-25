import os
import requests
import subprocess
import sys
import time

from midir import root_suffix

root_suffix("ydata_profile")

from src import ydata_profile
from src.ydata_profile import run_ydata_profile


def wait_for_server(port, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"http://localhost:{port}")
            if response.status_code == 200:
                return True
        except requests.ConnectionError:
            time.sleep(0.5)  # Wait a bit before retrying
    return False


def test_integration():

    cmd = [
        sys.executable, 
        "-m", 
        "streamlit", 
        "run", 
        "src/ydata_profile/streamlit_app.py"
    ]

    process = subprocess.Popen(cmd)
    print(f"Streamlit started in background with PID: {process.pid}")
    time.sleep(5)
    
    ports = [8501, 8502, 8503, 8504, 8505]
    for port in ports:
        if wait_for_server(port):
            print('Server is up.')
            assert True
            break
        time.sleep(5)
    else:
        raise AssertionError("Server failed to start within timeout")
    
    print("Time is up! Killing the process...")
    process.terminate()  # Sends SIGTERM (polite kill)
    
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()  # Sends SIGKILL (forced kill)
        print("Process forced to stop.")


test_integration()