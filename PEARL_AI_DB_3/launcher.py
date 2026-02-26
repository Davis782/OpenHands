import os
import sys
import subprocess
import traceback
from App.src.cli.cli_utils import _test_context

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

def run_streamlit_app():
    """Launches the Streamlit application."""
    print("Launching Streamlit application...")
    streamlit_path = os.path.join(PROJECT_ROOT, "App", "src", "ui", "main_app.py")
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", streamlit_path], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error launching Streamlit: {e}")
    except FileNotFoundError:
        print("Streamlit command not found. Please ensure Streamlit is installed (`pip install streamlit`).")

def run_cli_app(test_inputs: list[str] = None):
    """Launches the CLI application."""
    print("Launching CLI application...")
    from App.src.cli.main_cli_menu import main_menu as cli_main_menu

    if test_inputs:
        _test_context.activate_test_mode(test_inputs)

    try:
        cli_main_menu(test_mode=bool(test_inputs))
    except Exception as e:
        with open("full_cli_traceback.log", "w") as f:
            traceback.print_exc(file=f)
        print(f"An error occurred. Full traceback written to full_cli_traceback.log")
    finally:
        if test_inputs:
            _test_context.deactivate_test_mode()

def main_menu():
    """Displays the main menu and handles user input."""
    while True:
        print("\n--- PEARL AI Launcher ---")
        print("1. Launch Streamlit Application")
        print("2. Launch CLI Application")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == '1':
            run_streamlit_app()
        elif choice == '2':
            run_cli_app()
        elif choice == '3':
            print("Exiting launcher. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    print(f"sys.argv: {sys.argv}")
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        print("Launching CLI directly.")
        test_inputs = [
            "5", # Query Builder
            "4", # Build DELETE Query
            "1", # Select the first table (assuming it exists)
            "5", # Back to Query Builder Menu
            "5", # Back to Main Menu
            "6"  # Exit
        ]
        run_cli_app(test_inputs=test_inputs)
    else:
        print("Launching interactive menu.")
        main_menu()