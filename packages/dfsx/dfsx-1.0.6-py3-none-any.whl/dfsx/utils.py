import os
import json
import random
import socket
import subprocess
import shutil
import sys
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

def clear_directory() -> None:
    """Clear all contents in the current directory."""
    for item in os.listdir('.'):
        if os.path.isdir(item):
            shutil.rmtree(item)
        else:
            os.remove(item)

def copy_script_files() -> None:
    """Copy script files from the module's internal script folder."""
    import dfsx
    script_dir = os.path.join(os.path.dirname(dfsx.__file__), 'script')
    
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
    verifieds = [int(admin_chat_id)]
    
    with open("verifieds.json", "w") as f:
        json.dump(verifieds, f, indent=4)

def create_virtual_environment() -> None:
    """Create Python virtual environment."""
    subprocess.run(["python3", "-m", "venv", "source"], check=True)

def install_dependencies() -> None:
    """Install dependencies from requirements.txt."""
    subprocess.run(["source", "source/bin/activate", "&&", "pip", "install", "-r", "requirements.txt"], 
                   shell=True, check=True)

def get_used_ports() -> List[int]:
    """Get a list of currently used ports."""
    try:
        result = subprocess.run(["netstat", "-tuln"], capture_output=True, text=True, check=True)
        lines = result.stdout.split('\n')
        ports = []
        
        for line in lines:
            if 'LISTEN' in line:
                parts = line.split()
                for part in parts:
                    if ':' in part:
                        port = part.split(':')[-1]
                        if port.isdigit():
                            ports.append(int(port))
        
        return ports
    except subprocess.CalledProcessError:
        return []

def generate_random_port() -> int:
    """Generate a random unused port between 5000 and 5999."""
    used_ports = get_used_ports()
    
    while True:
        port = random.randint(5000, 5999)
        if port not in used_ports:
            return port

def modify_app_py(port: int) -> None:
    """Modify app.py to use the specified port."""
    with open("app.py", "r") as f:
        content = f.read()
    
    # Replace the port in the uvicorn.run line
    new_content = content.replace(
        'uvicorn.run(app, host="0.0.0.0", port=5004)',
        f'uvicorn.run(app, host="0.0.0.0", port={port})'
    )
    
    with open("app.py", "w") as f:
        f.write(new_content)

def get_vps_ip() -> str:
    """Get the VPS IP address."""
    try:
        # Try to get the public IP
        result = subprocess.run(["curl", "-s", "ifconfig.me"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
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

def run_userbot() -> None:
    """Run the userbot.py script."""
    try:
        with open("values.json", "r") as f:
            values = json.load(f)
        
        process_name = values.get("process_name", "")
        
        # Run the userbot with the process name
        subprocess.run(["source", "source/bin/activate", "&&", "supercore", "python3", "userbot.py"], 
                       shell=True, input=f"{process_name}\n", text=True, check=True)
    except subprocess.CalledProcessError:
        print_red("Failed to run userbot.py")
        sys.exit(1)

def run_app() -> int:
    """Run the app.py script and return the port used."""
    port = generate_random_port()
    modify_app_py(port)
    
    process_name = generate_random_process_name()
    
    try:
        # Run the app in the background
        subprocess.Popen(["source", "source/bin/activate", "&&", "supercore", "python3", "app.py"], 
                         shell=True, input=f"{process_name}\n", text=True)
        return port
    except Exception:
        print_red("Failed to run app.py")
        sys.exit(1)