import os
import json
import random
import socket
import subprocess
import shutil
import sys
import time
from typing import Dict, List, Optional, Tuple

def print_red(text: str) -> None:
    """Print text in red color."""
    print(f"\033[91m{text}\033[0m")

def print_green(text: str) -> None:
    """Print text in green color."""
    print(f"\033[92m{text}\033[0m")

def print_yellow(text: str) -> None:
    """Print text in yellow color."""
    print(f"\033[93m{text}\033[0m")

def get_user_input(prompt: str) -> str:
    """Get user input with a styled prompt."""
    print(f"\n┌─╼ {prompt}")
    user_input = input("└────╼ ❯❯❯ ")
    return user_input.strip()

def check_files_exist() -> bool:
    """Check if required files exist and are not empty."""
    required_files = ["values.json", "verifieds.json", "app.py"]
    
    for file in required_files:
        if not os.path.exists(file) or os.path.getsize(file) == 0:
            return False
    
    return True

def get_venv_env() -> dict:
    """
    Returns an environment dictionary modified to use the local 'source' venv.
    This is the programmatic way to "activate" a venv for a subprocess.
    """
    venv_path = os.path.join(os.getcwd(), "source")
    if not os.path.exists(venv_path):
        raise FileNotFoundError("Virtual environment 'source' not found.")
    
    venv_bin = os.path.join(venv_path, "bin")
    
    env = os.environ.copy()
    # Prepend venv's bin directory to PATH so 'python3', 'pip', 'supercore' etc. are found there first.
    env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"
    # Set VIRTUAL_ENV variable, which many tools (like pip) use.
    env["VIRTUAL_ENV"] = venv_path
    # Remove PYTHONHOME if set, as it can interfere with the venv.
    env.pop("PYTHONHOME", None)
    
    return env

def get_used_ports() -> List[int]:
    """Get a list of currently used ports."""
    try:
        # Using 'ss' is more modern and reliable than 'netstat'
        result = subprocess.run(["ss", "-tuln"], capture_output=True, text=True, check=True)
        lines = result.stdout.split('\n')
        ports = []
        
        for line in lines:
            if 'LISTEN' in line:
                parts = line.split()
                for part in parts:
                    if ':' in part and '.' not in part.split(':')[0]: # Avoid IPv6 for simplicity
                        port_str = part.split(':')[-1]
                        if port_str.isdigit():
                            ports.append(int(port_str))
        
        return ports
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to an empty list if ss command fails or is not found
        return []

def generate_random_port() -> int:
    """Generate a random unused port between 5000 and 5999."""
    used_ports = get_used_ports()
    
    for _ in range(20): # Try 20 times to find a free port
        port = random.randint(5000, 5999)
        if port not in used_ports:
            return port
            
    print_red("Could not find a free port in the range 5000-5999. Defaulting to 5004.")
    return 5004

def modify_app_py(port: int) -> None:
    """Modify app.py to use the specified port."""
    try:
        with open("app.py", "r") as f:
            content = f.read()
        
        # Use regex for a more robust replacement
        import re
        pattern = r'uvicorn\.run\(app,\s*host="0\.0\.0\.0",\s*port=\d+\)'
        replacement = f'uvicorn.run(app, host="0.0.0.0", port={port})'
        
        new_content = re.sub(pattern, replacement, content)
        
        with open("app.py", "w") as f:
            f.write(new_content)
    except FileNotFoundError:
        print_red("app.py not found. Cannot modify port.")
        sys.exit(1)

def get_vps_ip() -> str:
    """Get the VPS IP address."""
    try:
        # Try to get the public IP
        result = subprocess.run(["curl", "-s", "ifconfig.me"], capture_output=True, text=True, check=True, timeout=5)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    try:
        # Fallback to local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def run_app_supercore() -> Tuple[int, str]:
    """Run the app.py script with supercore and return the port used and process name."""
    port = generate_random_port()
    modify_app_py(port)
    
    try:
        env = get_venv_env()
        
        print_yellow("Starting web application with supercore...")
        process_name = get_user_input("Enter process name")
        
        # Run app.py with supercore in the background
        command = ["supercore", "python3", "app.py"]
        subprocess.Popen(command, env=env)
        
        return port, process_name
    except Exception as e:
        print_red(f"Failed to run app.py with supercore: {e}")
        sys.exit(1)

def main():
    """Main function to run the app with supercore."""
    # Check if required files exist
    if not check_files_exist():
        print_red("Required files are missing. Please ensure values.json, verifieds.json, and app.py exist.")
        sys.exit(1)
    
    # Run app with supercore
    port, process_name = run_app_supercore()
    vps_ip = get_vps_ip()
    
    # Wait 2 seconds
    time.sleep(2)
    
    # Print success message
    print_green("\nSCRIPT HAS RUNNED\n")
    print_green(f"PANEL: http://{vps_ip}:{port}")
    
    # Exit the program
    sys.exit(0)

if __name__ == "__main__":
    main()