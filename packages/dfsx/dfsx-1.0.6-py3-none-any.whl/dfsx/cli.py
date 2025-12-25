import os
import sys
from .utils import (
    print_red, print_green, print_yellow,
    get_user_input, check_files_exist, clear_directory,
    copy_script_files, create_values_json, create_verifieds_json,
    create_virtual_environment, install_dependencies,
    run_userbot, run_app, get_vps_ip, create_meta_output_json
)

def setup_mode():
    """Handle the setup mode when files are missing or empty."""
    print_yellow("\nDFSX Setup Mode")
    print_yellow("Please provide the following information:\n")
    
    # Get user inputs
    api_id = get_user_input("ENTER API ID")
    api_hash = get_user_input("ENTER API HASH")
    bot_token = get_user_input("ENTER BOT TOKEN")
    process_name = get_user_input("ENTER PROCESS NAME")
    admin_chat_id = get_user_input("ENTER ADMIN CHAT ID")
    
    # Clear directory and copy script files
    print_yellow("\nSetting up the environment...")
    clear_directory()
    copy_script_files()
    
    # Create configuration files
    create_values_json(api_id, api_hash, bot_token, process_name)
    create_verifieds_json(admin_chat_id)
    
    # Set up virtual environment and install dependencies
    print_yellow("Creating virtual environment and installing dependencies...")
    create_virtual_environment()
    install_dependencies()
    
    print_green("\nScript Loaded Successfully")

def run_mode():
    """Handle the run mode when all files exist."""
    print_yellow("\nDFSX Run Mode")
    print_yellow("Starting the bot and web application...\n")
    
    # Run userbot
    print_yellow("Starting userbot...")
    run_userbot()
    
    # Run app
    print_yellow("Starting web application...")
    port = run_app()
    vps_ip = get_vps_ip()
    process_name = os.environ.get('PROCESS_NAME', 'unknown')
    
    # Create meta output
    create_meta_output_json(vps_ip, port, process_name)
    
    # Print success message
    print_green("\nSCRIPT HAS RUNNED\n")
    print_green(f"PANEL: http://{vps_ip}:{port}")

def main():
    """Main entry point for the CLI."""
    # Check if running in /root directory
    if os.getcwd() == "/root":
        print_red("\nPlease Use in Particular Folder\n")
        sys.exit(1)
    
    # Check if required files exist
    if check_files_exist():
        run_mode()
    else:
        setup_mode()

if __name__ == "__main__":
    main()