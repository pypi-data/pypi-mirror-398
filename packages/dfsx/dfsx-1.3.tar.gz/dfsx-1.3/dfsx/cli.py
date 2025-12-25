import os
import sys
import time
from .utils import (
    print_red, print_green, print_yellow,
    get_user_input, check_files_exist,
    get_venv_env, get_used_ports, generate_random_port,
    modify_app_py, get_vps_ip, run_app_supercore
)

def run_mode():
    """Handle the run mode when all files exist."""
    print_yellow("\nDFSX Run Mode")
    
    # This function from utils.py handles port generation, app modification,
    # getting the process name from the user, and starting the app.
    port, process_name = run_app_supercore()
    
    # Wait 2 seconds after the app has been started
    time.sleep(2)
    
    # Get VPS IP to display in the final message
    vps_ip = get_vps_ip()
    
    # Print success message
    print_green("\nSCRIPT HAS RUNNED\n")
    print_green(f"PANEL: http://{vps_ip}:{port}")
    
    # Exit the program
    sys.exit(0)

def main():
    """Main entry point for the CLI."""
    # Check if running in /root directory
    if os.getcwd() == "/root":
        print_red("\nPlease Use in Particular Folder\n")
        sys.exit(1)
    
    # Check if required files exist
    if check_files_exist():
        # If files exist, proceed with the run mode
        run_mode()
    else:
        # If files are missing, print an error and exit.
        # The setup mode has been removed to match the simplified utils.py.
        print_red("\nRequired files (values.json, verifieds.json, app.py) are missing or empty.")
        print_red("Cannot run. Please ensure the project is set up correctly in this directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()