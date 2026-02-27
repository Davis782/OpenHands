import subprocess
import os

def run_cli():
    """
    Launches the CLI application.
    """
    print("Launching CLI Menu...")
    cli_path = os.path.join("App", "src", "main.py")
    subprocess.run(["python", cli_path])

def run_streamlit():
    """
    Launches the Streamlit UI.
    """
    print("Launching Streamlit UI...")
    streamlit_path = os.path.join("App", "src", "ui", "main_app.py")
    subprocess.run(["streamlit", "run", streamlit_path])

def main():
    """
    Presents a menu to the user to choose between CLI and Streamlit.
    """
    while True:
        print("\nSelect an option to launch:")
        print("1. Launch CLI Menu")
        print("2. Launch Streamlit UI")
        print("3. Exit")

        choice = input("Enter your choice (1-3): ")

        if choice == '1':
            run_cli()
        elif choice == '2':
            run_streamlit()
        elif choice == '3':
            print("Exiting application.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()