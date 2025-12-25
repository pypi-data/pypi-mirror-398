import os
import json
import random
import socket
import subprocess
import shutil
import sys
import time
import threading
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
    required_files = ["values.json", "verifieds.json", "app.py", "userbot.py"]
    
    for file in required_files:
        if not os.path.exists(file) or os.path.getsize(file) == 0:
            return False
    
    return True

def check_session_files() -> bool:
    """Check if any .session file exists in the current directory."""
    for file in os.listdir('.'):
        if file.endswith('.session'):
            return True
    return False

def clear_directory() -> None:
    """Clear all contents in the current directory."""
    for item in os.listdir('.'):
        # Avoid deleting the 'source' venv folder if it exists in a run-mode scenario
        # that somehow fails. In setup mode, it won't exist yet.
        if item == "source" and os.path.isdir(item):
            continue
        if os.path.isdir(item):
            shutil.rmtree(item)
        else:
            os.remove(item)

def copy_script_files() -> None:
    """Copy script files from the module's internal script folder."""
    import dfsx
    # Get the path to the installed dfsx package
    package_dir = os.path.dirname(dfsx.__file__)
    script_dir = os.path.join(package_dir, 'script')
    
    for item in os.listdir(script_dir):
        src = os.path.join(script_dir, item)
        dst = os.path.join(os.getcwd(), item)
        
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

def create_values_json(api_id: str, api_hash: str, bot_token: str, process_name: str) -> None:
    """Create values.json with user inputs."""
    values = {
        "api_id": api_id,
        "api_hash": api_hash,
        "bot_token": bot_token,
        "process_name": process_name
    }
    
    with open("values.json", "w") as f:
        json.dump(values, f, indent=4)

def create_verifieds_json(admin_chat_id: str) -> None:
    """Create verifieds.json with admin chat ID."""
    try:
        verifieds = [int(admin_chat_id)]
    except ValueError:
        print_red("Invalid Admin Chat ID. It must be a number.")
        sys.exit(1)
        
    with open("verifieds.json", "w") as f:
        json.dump(verifieds, f, indent=4)

def create_virtual_environment() -> None:
    """Create Python virtual environment."""
    print_yellow("Creating virtual environment 'source'...")
    subprocess.run([sys.executable, "-m", "venv", "source"], check=True)

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

def install_dependencies() -> None:
    """Install dependencies from requirements.txt."""
    try:
        command = ["pip", "install", "-r", "requirements.txt"]
        # Get the modified environment to use the venv's pip
        env = get_venv_env()
        print_yellow("Installing dependencies...")
        subprocess.run(command, env=env, check=True, capture_output=True, text=True)
    except FileNotFoundError as e:
        print_red(f"Error: {e}")
        print_red("Please run 'dfsx' in setup mode first to create the virtual environment.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print_red("Failed to install dependencies.")
        print_red(f"Error output: {e.stderr}")
        sys.exit(1)

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

def generate_random_process_name() -> str:
    """Generate a random 6-digit process name."""
    return str(random.randint(100000, 999999))

def create_meta_output_json(vps_ip: str, port: int, process_name: str) -> None:
    """Create meta_output.json with runtime information."""
    meta = {
        "vps_ip": vps_ip,
        "port": port,
        "process_name": process_name,
        "panel_url": f"http://{vps_ip}:{port}"
    }
    
    with open("meta_output.json", "w") as f:
        json.dump(meta, f, indent=4)

def monitor_session_files(callback):
    """Monitor the directory for .session files and call the callback when one is created."""
    print_yellow("Monitoring for session files...")
    
    # Check every 2 seconds for a new session file
    while not check_session_files():
        time.sleep(2)
    
    # Session file detected, call the callback
    print_green("\nSession file detected!")
    callback()

def run_userbot_first_time() -> None:
    """Run the userbot.py script for the first time without supercore."""
    try:
        env = get_venv_env()
        
        print_yellow("Starting userbot for the first time...")
        print_yellow("Please enter the required information when prompted.")
        
        # Run userbot.py directly with python3 (not supercore)
        # This allows the user to interact with the prompts directly
        command = ["python3", "userbot.py"]
        subprocess.run(command, env=env, check=True)
        
    except FileNotFoundError as e:
        print_red(f"Error: {e}")
        print_red("Ensure the virtual environment is set up correctly.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print_red("Failed to run userbot.py")
        print_red(f"Error output: {e.stderr}")
        sys.exit(1)

def run_userbot_supercore() -> None:
    """Run the userbot.py script with supercore."""
    try:
        env = get_venv_env()
        
        print_yellow("Starting userbot with supercore...")
        print_yellow("Please enter the process name when prompted.")
        
        # Run userbot.py with supercore
        command = ["supercore", "python3", "userbot.py"]
        subprocess.run(command, env=env, check=True)
        
    except FileNotFoundError as e:
        print_red(f"Error: {e}")
        print_red("Ensure the virtual environment is set up correctly and supercore is installed.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print_red("Failed to run userbot.py with supercore")
        print_red(f"Error output: {e.stderr}")
        sys.exit(1)

def run_app_supercore() -> int:
    """Run the app.py script with supercore and return the port used."""
    port = generate_random_port()
    modify_app_py(port)
    
    try:
        env = get_venv_env()
        
        print_yellow("Starting web application with supercore...")
        print_yellow("Please enter the process name when prompted.")
        
        # Run app.py with supercore
        command = ["supercore", "python3", "app.py"]
        subprocess.run(command, env=env, check=True)
        
        return port
    except Exception as e:
        print_red(f"Failed to run app.py with supercore: {e}")
        sys.exit(1)

def run_supercore_commands():
    """Run both userbot and app with supercore after session file is detected."""
    # Run userbot with supercore
    run_userbot_supercore()
    
    # Run app with supercore
    port = run_app_supercore()
    vps_ip = get_vps_ip()
    process_name = "unknown"  # We don't know the process name as the user entered it
    
    # Create meta output
    create_meta_output_json(vps_ip, port, process_name)
    
    # Print success message
    print_green("\nSCRIPT HAS RUNNED\n")
    print_green(f"PANEL: http://{vps_ip}:{port}")