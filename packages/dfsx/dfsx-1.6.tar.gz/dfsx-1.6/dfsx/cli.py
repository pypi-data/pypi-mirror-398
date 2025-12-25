import os
import sys
from .utils import (
    print_red, print_green, print_yellow,
    get_user_input, check_files_exist, check_session_files, clear_directory,
    copy_script_files, create_values_json, create_verifieds_json,
    create_virtual_environment, install_dependencies,
    run_userbot_first_time, monitor_session_files, run_supercore_commands
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
    
    # Check if session files exist
    if check_session_files():
        print_yellow("Session files detected. Running with supercore...")
        # Session files exist, run both userbot and app with supercore
        run_supercore_commands()
    else:
        print_yellow("No session files detected. Starting userbot for the first time...")
        # No session files, run userbot for the first time
        run_supercore_commands()
        
        # Start monitoring for session files in a separate thread
        monitor_thread = threading.Thread(target=monitor_session_files, args=(run_supercore_commands,))
        monitor_thread.daemon = True  # This allows the main thread to exit even if this thread is still running
        monitor_thread.start()
        
        print_green("\nUserbot started. Waiting for session file to be created...")
        print_green("Once the session file is created, dfsx will automatically run the supercore commands.")
        print_green("You can press Ctrl+C to exit if needed.")
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print_yellow("\nExiting dfsx...")
            sys.exit(0)

def main():
    """Main entry point for the CLI."""
    
    # Check if running in /root directory
    if os.getcwd() == "/root":
        print_red("\nPlease Use in Particular Folder\n")
        sys.exit(1)

    # If required files already exist
    if check_files_exist():
        print_red("\nDirectory Have already Loaded\n")
        sys.exit(0)

    # If files do NOT exist → setup mode
    setup_mode()

if __name__ == "__main__":
    main()